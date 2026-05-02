"""
Эндпоинты для задач (Канбан-доска) внутри чатов.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import TaskStatus
from app.crud.crud_chat import is_chat_member
from app.crud.crud_task import (
    create_task, get_chat_tasks, get_task_by_id,
    update_task, delete_task, convert_message_to_task, search_chat_tasks,
)
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/chats/{chat_id}/tasks", tags=["Задачи"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_new_task(
    chat_id: int,
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать задачу на доске чата."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await create_task(db, chat_id, current_user.id, task_in)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    chat_id: int,
    status_filter: Optional[TaskStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить задачи чата (фильтр по статусу: todo, in_progress, done)."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await get_chat_tasks(db, chat_id, status_filter)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    chat_id: int,
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить задачу (статус, дедлайн, приоритет и т.д.)."""
    task = await get_task_by_id(db, task_id)
    if not task or task.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return await update_task(db, task, task_in)


@router.delete("/{task_id}", status_code=204)
async def remove_task(
    chat_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить задачу."""
    task = await get_task_by_id(db, task_id)
    if not task or task.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await delete_task(db, task)


@router.post("/from-message", response_model=TaskResponse, status_code=201)
async def create_task_from_message(
    chat_id: int,
    message_id: int,
    title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Конвертация «Сообщение → Задача»."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await convert_message_to_task(db, chat_id, message_id, current_user.id, title)
