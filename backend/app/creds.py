# backend/app/creds.py
from google_auth_oauthlib.flow import Flow
from pathlib import Path
import os

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


# ❗❗❗ ここだけ修正が必要
# from gmail_service import get_user_token_path  ←✗ 動かない
# 相対インポートに変更
from app.gmail_service import get_user_token_path  # 再利用


def fetch_token(authorization_response: str, user_id: str):
    """認証コードからトークンを取得して保存"""
    flow = get_flow()

    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    token_path = get_user_token_path(user_id)
    token_path.parent.mkdir(exist_ok=True, parents=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")

    print(f"✅ トークン保存完了: {token_path}")
    return credentials


def has_valid_token(user_id: str) -> bool:
    """ユーザーのトークンが存在するか確認"""
    token_path = get_user_token_path(user_id)
    return token_path.exists()

