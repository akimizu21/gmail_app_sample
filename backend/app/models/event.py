# app/models/event.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    source_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)

    title = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # "面接" / "説明会" など
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    status = Column(String, default="draft")     # "draft" / "confirmed" など
    source = Column(String, default="auto")      # "auto" / "manual" など

    user = relationship("User", back_populates="events")
    email = relationship("Email")

