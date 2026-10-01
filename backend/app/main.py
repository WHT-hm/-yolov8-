from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine, SessionLocal
from .routers import auth, dashboard, detections, meta, settings, organizations, realtime, judgment
from . import auth as auth_module

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
(STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)

# 创建所有表
Base.metadata.create_all(bind=engine)

# 初始化超级管理员（如需要的话）
db = SessionLocal()
try:
    auth_module.ensure_super_admin(db)
finally:
    db.close()

app = FastAPI(title="农作物病虫害检测系统 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(detections.router)
app.include_router(meta.router)
app.include_router(organizations.router)
app.include_router(realtime.router)
app.include_router(judgment.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
