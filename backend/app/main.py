from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.settings import SESSION_SECRET_KEY, FRONTEND_BASE_URL
from app.api.auth import router as auth_router
from app.api.gmail import router as gmail_router
from app.api.events import router as events_router  # events_router を使う


app = FastAPI(
    title="JobSync API",
    version="0.1.0",
)

# ★ ここで app.include_router(events.router) は不要なので削除


# --- CORS 設定 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_BASE_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- セッションミドルウェア ---
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=True,
)

app.include_router(auth_router, prefix="/api")
app.include_router(gmail_router, prefix="/api")
app.include_router(events_router, prefix="/api")  # ここで /api/events が生える


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
