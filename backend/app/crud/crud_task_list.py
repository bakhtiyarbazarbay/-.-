"""
CRUD-операции для личных списков задач (Task Lists).
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskList
from app.schemas.task import TaskListCreate


async def create_task_list(
    db: AsyncSession, user_id: int, list_in: TaskListCreate
) -> TaskList:
    """Создать личный список задач."""
    task_list = TaskList(
        name=list_in.name,
        user_id=user_id,
    )
    db.add(task_list)
    await db.commit()
    await db.refresh(task_list)
    return task_list


async def get_user_task_lists(
    db: AsyncSession, user_id: int
) -> List[TaskList]:
    """Получить все списки задач пользователя."""
    result = await db.execute(
        select(TaskList)
        .where(TaskList.user_id == user_id)
        .order_by(TaskList.created_at.desc())
    )
    return result.scalars().all()


async def get_task_list_by_id(
    db: AsyncSession, list_id: int
) -> Optional[TaskList]:
    """Получить список задач по ID."""
    return await db.get(TaskList, list_id)


async def delete_task_list(
    db: AsyncSession, task_list: TaskList
) -> None:
    """Удалить личный список задач."""
    await db.delete(task_list)
    await db.commit()
