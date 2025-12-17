# backend/app/services/gmail_sync.py

from datetime import datetime
from zoneinfo import ZoneInfo
import re
from hashlib import sha256
from email.utils import parsedate_to_datetime

from sqlalchemy.orm import Session

from app.models.email import Email
from app.models.event import Event
from app.gmail_service import get_emails  # ★ ここを get_emails に
from app.services.company_parser import extract_company_name

JST = ZoneInfo("Asia/Tokyo")





def _parse_gmail_date(date_str: str | None) -> datetime:
    """
    Gmail の Date ヘッダ文字列を datetime(JST) に変換するヘルパー
    """
    if not date_str:
        # 日付が取れない場合は「今」にしておく（適当でOK）
        return datetime.now(JST)

    dt = parsedate_to_datetime(date_str)  # タイムゾーン付き or naive
    if dt.tzinfo is None:
        # タイムゾーン情報がなければ JST とみなす
        return dt.replace(tzinfo=JST)
    else:
        # 何かしらの tz が付いている場合は JST に変換
        return dt.astimezone(JST)


def sync_gmail_messages(db: Session, user_id: int) -> list[Event]:
    """
    1. Gmail API からメッセージ一覧を取得（get_emails）
    2. emails テーブルに upsert
    3. processing_status='queued' のメールから events を生成
    """
    # ==== ① Gmail からメッセージ一覧 ====
    # get_emails は user_id を文字列として扱っているので str() しておく
    gmail_messages = get_emails(str(user_id), max_results=50)

    for gm in gmail_messages:
        # gm: dict
        #   - gm["id"], gm["date"], gm["from"], gm["subject"], gm["snippet"], gm["body"]
        email = _upsert_email(db, user_id, gm)

        if email.processing_status == "queued":
            _parse_email_to_event(db, user_id, email)

    # 最後にユーザーのイベント一覧を返す
    events = (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.start_at)
        .all()
    )
    return events


def _upsert_email(db: Session, user_id: int, gm: dict) -> Email:
    """
    Gmail から取得した 1 通のメール(gm)を emails テーブルに保存 or 更新
    """
    gmail_message_id = gm["id"]
    received_at = _parse_gmail_date(gm.get("date"))

    email = (
        db.query(Email)
        .filter(
            Email.user_id == user_id,
            Email.gmail_message_id == gmail_message_id,
        )
        .first()
    )

    if email is None:
        email = Email(
            user_id=user_id,
            gmail_message_id=gmail_message_id,
            received_at=received_at,
            from_address=gm.get("from"),
            subject=gm.get("subject"),
            snippet=gm.get("snippet"),
            body_plain=gm.get("body"),
            processing_status="queued",
        )
        db.add(email)
    else:
        # 必要に応じて更新（件名やスニペットが変わることはほぼないけど一応）
        email.snippet = gm.get("snippet") or email.snippet
        email.subject = gm.get("subject") or email.subject

    db.commit()
    db.refresh(email)
    return email

def _parse_email_to_event(db: Session, user_id: int, email: Email) -> None:
    """
    emails テーブルに保存された 1 通のメールから、events を 0 or 1 件生成/更新
    """
    subject = email.subject or ""
    body = email.body_plain or ""
    text = subject + "\n" + body

    # 就活っぽいメールだけ対象にする（暫定ルール）
    if not any(k in text for k in ["説明会", "面接", "選考", "インターン", "グループディスカッション", "GD"]):
        email.processing_status = "parsed"
        db.commit()
        return

    # -----------------------------
    # ① 日付・時刻抽出（まずは今の簡易版）
    # -----------------------------
    date_match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    time_match = re.search(r"(\d{1,2}):(\d{2})", text)
    if not date_match or not time_match:
        email.processing_status = "failed"
        db.commit()
        return

    y, m, d = map(int, date_match.groups())
    hh, mm = map(int, time_match.groups())
    start_at = datetime(y, m, d, hh, mm, tzinfo=JST)

    # -----------------------------
    # ② 会社名抽出（ここが最重要の差し替えポイント）
    # -----------------------------
    from_address = email.from_address or ""
    company = extract_company_name(subject=subject, body=body, from_address=from_address)

    # company が取れない場合の保険（NoneのままでOKなら不要）
    if company is None:
        company = None

    # -----------------------------
    # ③ タイトル（必要なら会社名を付け足す）
    # -----------------------------
    title = subject or "面接/説明会"

    # -----------------------------
    # ④ dedup_hash（重複登録防止）
    # -----------------------------
    base = f"{user_id}|{company}|{title}|{start_at.isoformat()}"
    dedup_hash = sha256(base.encode("utf-8")).hexdigest()

    now = datetime.now(JST)

    ev = (
        db.query(Event)
        .filter(Event.user_id == user_id, Event.dedup_hash == dedup_hash)
        .first()
    )

    if ev is None:
        ev = Event(
            user_id=user_id,
            email_id=email.id,
            company_name=company,
            title=title,
            event_type="interview",  # 後で賢くする
            start_at=start_at,
            end_at=None,
            location=None,
            memo=None,
            source="auto",
            status="scheduled",
            dedup_hash=dedup_hash,
            created_at=now,
            updated_at=now,
        )
        db.add(ev)
    else:
        # 既存があれば必要に応じて更新
        ev.company_name = company or ev.company_name
        ev.title = title or ev.title
        ev.updated_at = now

    email.processing_status = "parsed"
    db.commit()

