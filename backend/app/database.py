# backend/app/database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

# ★ ここで .env を読み込む（create_tables.py から呼んでも有効にする）
load_dotenv()

# まず .env から読む。なければ SQLite をデフォルトにする
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobsync.db")

# SQLite のときは connect_args が必要（ファイルロック関連の警告回避用）
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # Postgres 等の場合
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

