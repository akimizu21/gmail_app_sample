# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse
from pydantic import BaseModel

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.settings import GOOGLE_CLIENT_ID
from app.creds import has_valid_token

router = APIRouter(tags=["auth"])


class GoogleAuthRequest(BaseModel):
    token: str


@router.post("/auth/google")
async def google_auth(body: GoogleAuthRequest, request: Request):
    """Googleログイン (IDトークン検証)"""
    try:
        if not GOOGLE_CLIENT_ID:
            raise RuntimeError("GOOGLE_CLIENT_ID が設定されていません")

        idinfo = id_token.verify_oauth2_token(
            body.token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )

        user_info = {
            "google_sub": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name", ""),
        }

        # セッションに保存
        request.session["google_id"] = user_info["google_sub"]
        request.session["email"] = user_info["email"]
        request.session["name"] = user_info["name"]

        gmail_authorized = has_valid_token(user_info["google_sub"])

        return JSONResponse(
            {
                "message": "認証成功",
                "user": user_info,
                "gmail_authorized": gmail_authorized,
            }
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid token: {str(e)}"},
        )
    except Exception as e:
        print(f"認証エラー: {e!r}")
        return JSONResponse(
            status_code=500,
            content={"error": f"認証エラー: {str(e)}"},
        )


@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "ログアウトしました"}


@router.get("/user")
async def get_user(request: Request):
    """現在ログイン中のユーザー情報を取得"""
    session = request.session
    if "google_id" not in session:
        raise HTTPException(status_code=401, detail="未ログイン")

    gmail_authorized = has_valid_token(session["google_id"])

    return {
        "google_id": session["google_id"],
        "email": session.get("email"),
        "name": session.get("name"),
        "gmail_authorized": gmail_authorized,
    }
