# backend/app/core/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-secret-key")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
