# backend/app/create_tables.py
from app.database import Base, engine

# 🎯 ポイント：
#   モデルを「モジュールごと」import しておけば、
#   その中で宣言された User / Email / Event が Base に自動登録される
from app.models import user, email, event  # noqa: F401

# backend/app/create_tables.py

print("Creating tables...")

from app.database import Base, engine   # ★ ここから Base を取る
from app.models import user, email, event  # noqa: F401

Base.metadata.create_all(bind=engine)
print("Done.")


