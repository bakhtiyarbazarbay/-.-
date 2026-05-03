"""
Эндпоинты для личных списков задач.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import TaskStatus
from app.crud.crud_task_list import (
    create_task_list, get_user_task_lists, get_task_list_by_id, delete_task_list
)
from app.crud.crud_task import create_task, get_list_tasks, update_task, get_task_by_id
from app.schemas.task import TaskListCreate, TaskListResponse, TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/task-lists", tags=["Списки задач"])


@router.post("/", response_model=TaskListResponse, status_code=201)
async def create_new_task_list(
    list_in: TaskListCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новый личный список задач."""
    return await create_task_list(db, current_user.id, list_in)


@router.get("/", response_model=List[TaskListResponse])
async def list_my_task_lists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить все личные списки задач текущего пользователя."""
    return await get_user_task_lists(db, current_user.id)


@router.delete("/{list_id}", status_code=204)
async def remove_task_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить список задач."""
    task_list = await get_task_list_by_id(db, list_id)
    if not task_list or task_list.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Список не найден")
    await delete_task_list(db, task_list)


@router.post("/{list_id}/tasks/", response_model=TaskResponse, status_code=201)
async def add_task_to_list(
    list_id: int,
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать задачу внутри личного списка."""
    task_list = await get_task_list_by_id(db, list_id)
    if not task_list or task_list.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Список не найден")

    task_in.task_list_id = list_id
    return await create_task(db, None, current_user.id, task_in)


@router.get("/{list_id}/tasks/", response_model=List[TaskResponse])
async def get_tasks_in_list(
    list_id: int,
    status_filter: Optional[TaskStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить задачи из личного списка."""
    task_list = await get_task_list_by_id(db, list_id)
    if not task_list or task_list.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Список не найден")

    return await get_list_tasks(db, list_id, status_filter)


@router.put("/{list_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task_in_list(
    list_id: int,
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить задачу внутри личного списка."""
    task_list = await get_task_list_by_id(db, list_id)
    if not task_list or task_list.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Список не найден")

    task = await get_task_by_id(db, task_id)
    if not task or task.task_list_id != list_id:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return await update_task(db, task, task_in)
