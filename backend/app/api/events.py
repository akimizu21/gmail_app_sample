# backend/app/api/events.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventRead

router = APIRouter(tags=["events"])


@router.get("/events", response_model=List[EventRead])
async def list_events(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    ログインユーザーの Event 一覧を返す
    """
    events = (
        db.query(Event)
        .join(Event.user)
        .filter(Event.user.has(google_sub=user_id))
        .order_by(Event.start_at.is_(None), Event.start_at)
        .all()
    )
    return [EventRead.model_validate(ev) for ev in events]


@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(
    event_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    単一 Event の詳細
    """
    ev = (
        db.query(Event)
        .join(Event.user)
        .filter(Event.id == event_id, Event.user.has(google_sub=user_id))
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    return EventRead.model_validate(ev)

