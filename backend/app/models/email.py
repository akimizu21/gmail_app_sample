# app/models/email.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    gmail_message_id = Column(String, index=True, unique=True, nullable=False)
    from_address = Column(String)
    subject = Column(String)
    snippet = Column(Text)
    body_plain = Column(Text)
    received_at = Column(DateTime)
    processing_status = Column(String, default="queued")

    # ★ User 側の emails と対応させる
    user = relationship("User", back_populates="emails")

