# backend/app/core/deps.py
from fastapi import HTTPException, Request

def get_current_user_id(request: Request) -> str:
    """セッションから現在のユーザーID(google_id)を取り出す"""
    user_id = request.session.get("google_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="未ログイン")
    return user_id
