# backend/app/gmail_service.py
from googleapiclient.discovery import build
import base64

from app.creds import load_credentials

SCOPES = ["https://mail.google.com/"]


# ============================
# ヘルパ関数
# ============================

def get_header(headers, name: str):
    """ヘッダーから指定した名前の値を取得"""
    lname = name.lower()
    for h in headers:
        if h["name"].lower() == lname:
            return h["value"]
    return None


def base64_decode(data: str) -> str:
    """Base64デコード"""
    return base64.urlsafe_b64decode(data).decode(errors="ignore")


def get_body(body: dict | None):
    """本文を取得"""
    if not body:
        return None
    if body.get("size", 0) > 0 and "data" in body:
        return base64_decode(body["data"])
    return None


def get_parts_body(body: dict):
    """パーツから本文を取得"""
    if (
        body.get("size", 0) > 0
        and "data" in body
        and body.get("mimeType") == "text/plain"
    ):
        return base64_decode(body["data"])
    return None


def get_parts(parts: list[dict]):
    """パーツを再帰的に処理して本文を取得"""
    for part in parts:
        if part.get("mimeType") == "text/plain":
            body = part.get("body", {})
            if "data" in body:
                b = base64_decode(body["data"])
                if b is not None:
                    return b

        if "body" in part:
            b = get_parts_body(part["body"])
            if b is not None:
                return b

        if "parts" in part:
            b = get_parts(part["parts"])
            if b is not None:
                return b
    return None


def get_email_body(payload: dict):
    """メール本文を取得（統合関数）"""
    body = payload.get("body", {})
    body_data = get_body(body) if body.get("size", 0) > 0 else None

    parts_data = None
    if "parts" in payload:
        parts_data = get_parts(payload["parts"])

    return body_data if body_data is not None else parts_data


# ============================
# Gmail API
# ============================

def get_emails(user_id: int, max_results: int = 10):
    """
    DBに保存された Gmail token を使ってメールを取得
    
    Args:
        user_id: users.id（Integer）
        max_results: 取得するメール数
    
    Returns:
        メールのリスト
    """
    # ✅ DBからトークンを読み込む
    creds = load_credentials(user_id)

    service = build("gmail", "v1", credentials=creds)

    messages = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results)
        .execute()
        .get("messages", [])
    )

    email_list = []

    for message in messages:
        m_data = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )

        headers = m_data["payload"]["headers"]
        body_text = get_email_body(m_data["payload"])

        email_list.append({
            "id": message["id"],
            "date": get_header(headers, "date"),
            "from": get_header(headers, "from"),
            "to": get_header(headers, "to"),
            "subject": get_header(headers, "subject"),
            "snippet": m_data.get("snippet", ""),
            "body": body_text[:1000] if body_text else "",
        })

    return email_list