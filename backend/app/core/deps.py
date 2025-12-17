from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


def get_current_user_id(
    request: Request,
    db: Session = Depends(get_db),
) -> int:
    """セッションから現在のユーザーの DB user.id を返す"""
    google_sub = request.session.get("google_id")
    if not google_sub:
        raise HTTPException(status_code=401, detail="未ログイン")

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user.id   # ✅ Integer
