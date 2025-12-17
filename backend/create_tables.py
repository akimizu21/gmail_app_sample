# backend/create_tables.py
from app.database import engine, Base
from app.models.user import User
from app.models.event import Event
from app.models.email import Email  # 該当するモデルがあれば
from app.models.gmail_token import GmailToken

def create_tables():
    """全てのテーブルを作成"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    create_tables()
