# backend/app/api/gmail.py

from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.settings import FRONTEND_BASE_URL
from app.core.deps import get_current_user_id
from app.creds import get_authorization_url, fetch_token, has_valid_token
from app.gmail_service import get_emails
from app.database import get_db
from app.models.user import User
from app.models.email import Email
from app.models.event import Event
from app.schemas.event import EventRead

router = APIRouter(tags=["gmail"])


# ============================
# Gmail 認証フロー
# ============================

@router.get("/gmail/authorize")
async def gmail_authorize(request: Request):
    """Gmail認証を開始"""
    if "google_id" not in request.session:
        raise HTTPException(status_code=401, detail="先にログインしてください")

    authorization_url, state = get_authorization_url()
    request.session["oauth_state"] = state

    return {"authorization_url": authorization_url}


@router.get("/gmail/callback")
async def gmail_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    # デバック用ログ
    print("🔥🔥🔥 gmail_callback に到達しました")
    print("URL:", request.url)

    session = request.session
    if "google_id" not in session:
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/?error=not_logged_in"
        )

    google_sub = session["google_id"]

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        return RedirectResponse(
            url=f"{FRONTEND_BASE_URL}/dashboard?gmail_auth=user_not_found"
        )

    authorization_response = str(request.url)

    fetch_token(
        authorization_response=authorization_response,
        user_id=user.id, 
        db=db
    )

    return RedirectResponse(
        url=f"{FRONTEND_BASE_URL}/dashboard?gmail_auth=success"
    )


# ============================
# 生の Gmail メール取得（ダッシュボード表示用）
# ============================

@router.get("/gmail")
async def get_gmail_data(user_id: str = Depends(get_current_user_id)):
    """ログインユーザーのGmailを直接取得して返す（DBには保存しない）"""
    if not has_valid_token(user_id):
        raise HTTPException(
            status_code=401,
            detail={"error": "Gmail認証が必要です", "needs_auth": True},
        )

    try:
        emails = get_emails(user_id, max_results=10)
        return {"emails": emails}
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Gmail取得エラー: {str(e)}",
        )


# ============================
# ヘルパ（DB 保存／Event 自動生成 用）
# ============================

def _get_or_create_user(
    db: Session,
    google_sub: str,
    email_addr: str | None = None,
    name: str | None = None,
) -> User:
    """
    User テーブルに Google ユーザー情報を保存。
    主キーは user.id、Google の sub は user.google_sub という前提。
    """
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user:
        updated = False
        if email_addr and not user.email:
            user.email = email_addr
            updated = True
        if name and not user.name:
            user.name = name
            updated = True
        if updated:
            db.add(user)
        return user

    user = User(
        google_sub=google_sub,
        email=email_addr,
        name=name,
    )
    db.add(user)
    db.flush()
    return user


def _parse_received_at(header_date: str | None) -> datetime | None:
    if not header_date:
        return None
    try:
        dt = parsedate_to_datetime(header_date)
        return dt
    except Exception:
        return None


def _infer_event_type(subject: str | None) -> str:
    if not subject:
        return "その他"
    if "面接" in subject:
        return "面接"
    if "選考" in subject:
        return "面接"
    if "説明会" in subject or "セミナー" in subject:
        return "説明会"
    return "その他"


def _guess_company_from_subject(subject: str | None) -> str | None:
    if not subject:
        return None
    # すごく簡易なパターン：先頭の「〇〇株式会社」までを拾う
    m = re.search(r"(.+?株式会社)", subject)
    if m:
        return m.group(1)
    return None


def _make_event_from_email(email: Email) -> Event:
    """
    Email 行からざっくり Event を自動生成。
    日付・場所などの抽出ロジックはあとで強化予定。
    """
    subject = email.subject or "(件名なし)"
    event_type = _infer_event_type(subject)
    company = _guess_company_from_subject(subject)

    # ここでは start_at はとりあえず受信日時にしておく（あとで本文から抽出でもOK）
    start_at = email.received_at

    ev = Event(
        user_id=email.user_id,
        source_email_id=email.id,
        title=subject,
        company_name=company,
        event_type=event_type,
        start_at=start_at,
        status="draft",   # 下書き状態（ユーザーが後で編集・確定）
        source="auto",    # 自動生成
    )
    return ev


# ============================
# Gmail → DB 取込API
# ============================

# backend/app/api/gmail.py

@router.post("/gmail/import")
async def import_gmail(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """
    Gmail からメールを取得して DB（emails/events）に保存し、
    自動生成された Event の一覧を返す。
    """
    # セッションから email / name を取れるなら User 作成時に使う
    session = request.session
    session_email = session.get("email")
    session_name = session.get("name")

    print("=== /api/gmail/import called ===")
    print(f"  user_id (google_sub): {user_id}")
    print(f"  session email: {session_email}, name: {session_name}")

    user = _get_or_create_user(
        db,
        google_sub=user_id,
        email_addr=session_email,
        name=session_name,
    )
    print(f"  DB user.id = {user.id}")

    # Gmail API から実際のメールを取得
    messages = get_emails(user_id, max_results=20)  # 例として 20件
    print(f"  Gmail messages fetched: {len(messages)}")

    imported_emails = 0
    new_events: List[Event] = []

    for idx, m in enumerate(messages):
        print(f"--- message #{idx} ---")
        print(f"  keys: {list(m.keys())}")
        print(f"  id: {m.get('id')}, subject: {m.get('subject')!r}")

        gmail_id = m["id"]

        # すでに取り込み済みならスキップ（デバッグ表示付き）
        exists = (
            db.query(Email)
            .filter(Email.user_id == user.id, Email.gmail_message_id == gmail_id)
            .first()
        )
        if exists:
            print(f"  -> already exists in DB (email.id={exists.id}), skip")
            continue

        email_obj = Email(
            user_id=user.id,
            gmail_message_id=gmail_id,
            from_address=m.get("from"),
            subject=m.get("subject"),
            snippet=m.get("snippet"),
            body_plain=m.get("body"),
            received_at=_parse_received_at(m.get("date")),
            processing_status="queued",
        )
        db.add(email_obj)
        db.flush()  # email_obj.id を取るため
        print(f"  -> inserted Email.id={email_obj.id}")

        imported_emails += 1

        # とりあえず全メールから Event を作ってみる
        ev = _make_event_from_email(email_obj)
        if ev:
            db.add(ev)
            new_events.append(ev)
            print(f"  -> created Event (title={ev.title!r})")

    db.commit()
    print(f"=== /api/gmail/import DONE: imported_emails={imported_emails}, new_events={len(new_events)} ===")

    return {
        "imported_emails": imported_emails,
        "new_events": [EventRead.from_orm(ev) for ev in new_events],
    }
