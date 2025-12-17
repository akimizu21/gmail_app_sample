# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.settings import GOOGLE_CLIENT_ID
from app.creds import has_valid_token
from app.database import get_db
from app.models.user import User

router = APIRouter(tags=["auth"])


class GoogleAuthRequest(BaseModel):
    token: str


@router.post("/auth/google")
async def google_auth(body: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
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

        google_sub = idinfo["sub"]

        user = db.query(User).filter(User.google_sub == google_sub).first()
        if not user:
            user = User(
                google_sub=google_sub,
                email=idinfo.get("email"),
                name=idinfo.get("name",""),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # セッションに保存
        request.session["google_id"] = google_sub
        request.session["email"] = user.email
        request.session["name"] = user.name

        gmail_authorized = has_valid_token(user.id)

        return JSONResponse(
            {
                "message": "認証成功",
                 "user": {
                    "id": user.id,
                    "google_sub": user.google_sub,
                    "email": user.email,
                    "name": user.name,
                },
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
