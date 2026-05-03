"""
Google Antigravity — Backend API.
Гибридная система коммуникаций и менеджмента задач для университетов.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import auth, users, chats, tasks, task_lists, websocket
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend для гибридной системы коммуникаций и менеджмента задач. "
        "Интегрирует мессенджер (чаты, каналы, ветки) и Канбан-доски задач."
    ),
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Подключение роутеров ──────────────────────────────────────
API_PREFIX = settings.API_V1_STR

os.makedirs("uploads", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(chats.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(task_lists.router, prefix=API_PREFIX)
app.include_router(websocket.router)  # WebSocket — без API-префикса


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
