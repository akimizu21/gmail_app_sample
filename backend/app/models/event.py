# app/models/event.py
from sqlalchemy import (
    Column, Integer, Text, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"

    # 🔁 ここを BigInteger → Integer に統一
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)

    company_name = Column(Text)
    title = Column(Text, nullable=False)
    event_type = Column(String(16), nullable=False, default="other")  # interview / briefing / other
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True))
    location = Column(Text)
    memo = Column(Text)

    source = Column(String(16), nullable=False, default="auto")       # auto / manual
    status = Column(String(16), nullable=False, default="scheduled")  # scheduled / cancelled / done
    dedup_hash = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # ★ リレーション
    user  = relationship("User",  back_populates="events")
    email = relationship("Email", back_populates="events")
