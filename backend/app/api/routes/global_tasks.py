"""
Глобальные эндпоинты задач пользователя (Smart Lists, Inbox).
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.crud.crud_task import get_global_tasks_for_user, create_task
from app.schemas.task import TaskResponse, TaskCreate

router = APIRouter(prefix="/tasks/me", tags=["Глобальные задачи"])

@router.get("/all", response_model=List[TaskResponse])
async def get_all_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Все задачи пользователя."""
    return await get_global_tasks_for_user(db, current_user.id, "all")

@router.get("/today", response_model=List[TaskResponse])
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Задачи на сегодня."""
    return await get_global_tasks_for_user(db, current_user.id, "today")

@router.get("/upcoming", response_model=List[TaskResponse])
async def get_upcoming_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Задачи на ближайшие 7 дней."""
    return await get_global_tasks_for_user(db, current_user.id, "upcoming")

@router.get("/inbox", response_model=List[TaskResponse])
async def get_inbox_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Задачи во входящих (без чата и списка)."""
    return await get_global_tasks_for_user(db, current_user.id, "inbox")

@router.post("/inbox", response_model=TaskResponse, status_code=201)
async def create_inbox_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать задачу во Входящих (Inbox)."""
    task_in.chat_id = None
    task_in.task_list_id = None
    return await create_task(db, None, current_user.id, task_in)
