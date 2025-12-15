# backend/app/schemas/event.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    id: int
    user_id: int
    source_email_id: int | None = None
    title: str
    company_name: str | None = None
    event_type: str
    start_at: datetime | None = None
    end_at: datetime | None = None
    location: str | None = None
    status: str
    source: str | None = None
    created_at: datetime
    updated_at: datetime

    # ★ ORM オブジェクトからの変換を許可
    model_config = ConfigDict(from_attributes=True)
