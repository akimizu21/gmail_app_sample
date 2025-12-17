from sqlalchemy import (
    Column, Integer, Text, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base  # Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)  # autoincrement は省略でOK

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gmail_message_id = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    from_address = Column(Text)
    subject = Column(Text)
    snippet = Column(Text)
    processing_status = Column(String(16), nullable=False, default="queued")
    body_plain = Column(Text)

    user = relationship("User", back_populates="emails")
    events = relationship("Event", back_populates="email")

