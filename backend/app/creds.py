# backend/app/creds.py
# モジュールも一部追加
import os
import json
from pathlib import Path

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from sqlalchemy.orm import Session

from app.models.gmail_token import GmailToken
from app.database import SessionLocal


SCOPES = ['https://mail.google.com/']

BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def get_flow(redirect_uri: str | None = None) -> Flow:
    """OAuth Flowを作成"""
    if redirect_uri is None:
        redirect_uri = f"{BACKEND_BASE_URL}/api/gmail/callback"

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    # スコープ変更を許可
    flow.oauth2session._client.default_token_placement = 'query'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv(
        'OAUTHLIB_INSECURE_TRANSPORT', '1'
    )

    return flow


def get_authorization_url():
    """認証URLを取得"""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return authorization_url, state

# 以下追加したコード
# ============================
# Token 保存・取得（DB）
# ============================

def save_token_to_db(user_id: int, token_json: str):
    """Gmail token を DB に保存（upsert）"""
    db: Session = SessionLocal()
    try:
        token = db.query(GmailToken).filter_by(user_id=user_id).first()
        if token:
            token.token_json = token_json
        else:
            token = GmailToken(
                user_id=user_id,
                token_json=token_json,
            )
            db.add(token)

        db.commit()
    finally:
        db.close()


def fetch_token(
    authorization_response: str,
    user_id: str,
    db: Session
):
    flow = get_flow()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    token_json = credentials.to_json()

    token = db.get(GmailToken, user_id)
    if token:
        token.token_json = token_json
    else:
        token = GmailToken(
            user_id=user_id,
            token_json=token_json
        )
        db.add(token)

    db.commit()
    return credentials


def has_valid_token(user_id: int) -> bool:
    """
    DB に有効な Gmail token があるか確認
    - 有効 → True
    - 期限切れ + refresh_token あり → refresh して True
    - それ以外 → False
    """
    db: Session = SessionLocal()
    try:
        token = db.query(GmailToken).filter_by(user_id=user_id).first()
        if not token:
            return False

        creds = Credentials.from_authorized_user_info(
            json.loads(token.token_json)
        )

        if creds.valid:
            return True

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.token_json = creds.to_json()
            db.commit()
            return True

        return False
    finally:
        db.close()


def load_credentials(user_id: int) -> Credentials:
    """
    Gmail API 用の Credentials を DB から取得
    （gmail_service.py から利用）
    """
    db: Session = SessionLocal()
    try:
        token = db.query(GmailToken).filter_by(user_id=user_id).first()
        if not token:
            raise RuntimeError("Gmail token not found")

        return Credentials.from_authorized_user_info(
            json.loads(token.token_json)
        )
    finally:
        db.close()


# # ❗❗❗ ここだけ修正が必要
# # from gmail_service import get_user_token_path  ←✗ 動かない
# # 相対インポートに変更
# from app.gmail_service import get_user_token_path  # 再利用


# def fetch_token(authorization_response: str, user_id: str):
#     """認証コードからトークンを取得して保存"""
#     flow = get_flow()

#     flow.fetch_token(authorization_response=authorization_response)
#     credentials = flow.credentials

#     token_path = get_user_token_path(user_id)
#     token_path.parent.mkdir(exist_ok=True, parents=True)
#     token_path.write_text(credentials.to_json(), encoding="utf-8")

#     print(f"✅ トークン保存完了: {token_path}")
#     return credentials

# def has_valid_token(user_id: str) -> bool:
#     """ユーザーのトークンが存在するか確認"""
#     token_path = get_user_token_path(user_id)
#     return token_path.exists()

