# backend/app/api/gmail.py

from datetime import datetime, timezone
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
async def get_gmail_data(user_id: int = Depends(get_current_user_id)):
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

def _parse_received_at(header_date: str | None) -> datetime | None:
    if not header_date:
        return None
    try:
        dt = parsedate_to_datetime(header_date)
        return dt
    except Exception:
        return None


def _infer_event_type(subject: str | None) -> str:
    """件名からイベントタイプを推測"""
    if not subject:
        return "other"
    if "面接" in subject or "選考" in subject:
        return "interview"
    if "説明会" in subject or "セミナー" in subject:
        return "briefing"
    return "other"


def _guess_company_from_subject(subject: str | None) -> str | None:
    """件名から会社名を抽出"""
    if not subject:
        return None
    # 「〇〇株式会社」パターン
    m = re.search(r"(.+?株式会社)", subject)
    if m:
        return m.group(1)
    # 【】内のテキスト
    m = re.search(r"【(.+?)】", subject)
    if m:
        return m.group(1)
    return None


def _make_event_from_email(email: Email) -> Event | None:
    """
    Email からイベントを自動生成。
    面接・説明会関連のメールのみイベントを作成。
    """
    subject = email.subject or "(件名なし)"
    event_type = _infer_event_type(subject)
    
    # 面接・説明会以外はスキップ
    if event_type == "other":
        print(f"  -> Skipping (event_type=other): {subject}")
        return None
    
    company = _guess_company_from_subject(subject)
    now = datetime.now(timezone.utc)  # ✅ timezone-aware datetime
    start_at = email.received_at or now

    ev = Event(
        user_id=email.user_id,
        email_id=email.id,
        title=subject,
        company_name=company,
        event_type=event_type,
        start_at=start_at,
        status="scheduled",
        source="auto",
        created_at=now,      # ✅ 追加
        updated_at=now,      # ✅ 追加
    )
    return ev


# ============================
# Gmail → DB 取込API
# ============================

@router.post("/gmail/import")
async def import_gmail(
    request: Request,
    user_id: int = Depends(get_current_user_id),  # ✅ user.id (int)
    db: Session = Depends(get_db),
) -> dict:
    """
    Gmail からメールを取得して DB（emails/events）に保存し、
    自動生成された Event の一覧を返す。
    """
    print("=== /api/gmail/import called ===")
    print(f"  user_id: {user_id}")

    # ✅ user_id から直接 User を取得
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    print(f"  DB user.id = {user.id}, email = {user.email}")

    # Gmail API から実際のメールを取得
    messages = get_emails(user_id, max_results=20)
    print(f"  Gmail messages fetched: {len(messages)}")

    imported_emails = 0
    new_events: List[Event] = []

    for idx, m in enumerate(messages):
        gmail_id = m["id"]
        subject = m.get("subject", "(no subject)")
        print(f"--- message #{idx}: {subject[:50]}... ---")

        # すでに取り込み済みならスキップ
        exists = (
            db.query(Email)
            .filter(Email.user_id == user.id, Email.gmail_message_id == gmail_id)
            .first()
        )
        if exists:
            print(f"  -> already exists (email.id={exists.id}), skip")
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
        db.flush()
        print(f"  -> inserted Email.id={email_obj.id}")

        imported_emails += 1

        # イベント自動生成（面接・説明会のみ）
        ev = _make_event_from_email(email_obj)
        if ev:
            db.add(ev)
            new_events.append(ev)
            print(f"  -> created Event: {ev.event_type} - {ev.company_name}")

    db.commit()
    print(f"=== DONE: imported_emails={imported_emails}, new_events={len(new_events)} ===")

    return {
        "imported_emails": imported_emails,
        "new_events": [EventRead.from_orm(ev) for ev in new_events],
    }