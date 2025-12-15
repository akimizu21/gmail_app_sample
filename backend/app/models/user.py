# app/models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String, unique=True, index=True, nullable=False)

    email = Column(String, index=True, nullable=True)
    name = Column(String, nullable=True)

    # ★ ここを追加：Email / Event とのリレーション
    emails = relationship(
        "Email",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "Event",
        back_populates="user",
        cascade="all, delete-orphan",
    )
