"""
CRUD-операции для задач (Task Manager).
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(
    db: AsyncSession, chat_id: int, creator_id: int, task_in: TaskCreate
) -> Task:
    """Создать задачу, привязанную к чату."""
    task = Task(
        chat_id=chat_id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        created_by=creator_id,
        assigned_to=task_in.assigned_to,
        deadline=task_in.deadline,
        source_message_id=task_in.source_message_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_chat_tasks(
    db: AsyncSession,
    chat_id: int,
    status_filter: Optional[TaskStatus] = None,
) -> List[Task]:
    """Получить задачи чата (опционально фильтрация по статусу)."""
    query = select(Task).where(Task.chat_id == chat_id)
    if status_filter:
        query = query.where(Task.status == status_filter)
    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Получить задачу по ID."""
    return await db.get(Task, task_id)


async def update_task(
    db: AsyncSession, task: Task, task_in: TaskUpdate
) -> Task:
    """Обновить задачу (статус, описание, дедлайн и т.д.)."""
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    """Удалить задачу."""
    await db.delete(task)
    await db.commit()


async def convert_message_to_task(
    db: AsyncSession,
    chat_id: int,
    message_id: int,
    creator_id: int,
    title: str,
) -> Task:
    """Конвертация «Сообщение → Задача»."""
    task = Task(
        chat_id=chat_id,
        title=title,
        source_message_id=message_id,
        created_by=creator_id,
        status=TaskStatus.todo,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
