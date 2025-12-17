# backend/app/api/events.py
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id
from app.database import get_db
from app.schemas.event import EventRead, EventUpdate  # ★ EventUpdate を追加で用意してね
from app.models.event import Event
from app.services.gmail_sync import sync_gmail_messages

router = APIRouter(prefix="/events", tags=["events"])

JST = ZoneInfo("Asia/Tokyo")


@router.post("/sync", response_model=List[EventRead])
def sync_events(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Gmail からメールを同期して events を更新し、その一覧を返す
    """
    events = sync_gmail_messages(db, user_id)
    return events


@router.get("/", response_model=List[EventRead])
def list_events(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    現在登録されている予定一覧を返す
    """
    events = (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.start_at)
        .all()
    )
    return events


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    予定を 1 件取得
    """
    ev = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == user_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    予定を部分更新（編集）
    """
    ev = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == user_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    data = payload.model_dump(exclude_unset=True)

    # （任意）ユーザーが編集したら manual 扱いに寄せる
    if data:
        ev.source = "manual"

    # フィールド反映
    for k, v in data.items():
        setattr(ev, k, v)

    # updated_at 更新
    ev.updated_at = datetime.now(JST)

    db.commit()
    db.refresh(ev)
    return ev


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    予定を削除
    """
    ev = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == user_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(ev)
    db.commit()
    return {"ok": True}


