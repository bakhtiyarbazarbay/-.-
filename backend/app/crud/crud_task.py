"""
CRUD-операции для задач (Task Manager).
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(
    db: AsyncSession, chat_id: Optional[int], creator_id: int, task_in: TaskCreate
) -> Task:
    """Создать задачу, привязанную к чату или списку."""
    task = Task(
        chat_id=chat_id,
        task_list_id=task_in.task_list_id,
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


async def search_chat_tasks(
    db: AsyncSession, chat_id: int, query: str, limit: int = 50
) -> List[Task]:
    """Поиск задач в чате по названию или описанию (без учета регистра)."""
    from sqlalchemy import or_
    result = await db.execute(
        select(Task)
        .where(Task.chat_id == chat_id)
        .where(
            or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%")
            )
        )
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


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


async def get_global_tasks_for_user(
    db: AsyncSession,
    user_id: int,
    filter_type: str = "all"
) -> List[Task]:
    """
    Получить глобальные задачи для пользователя.
    filter_type: "all", "today", "upcoming" (next 7 days), "inbox"
    """
    from datetime import datetime, timedelta, timezone
    from app.models.chat import chat_members
    from app.models.task import TaskList

    # Базовый запрос: задачи, где пользователь создатель, назначенец,
    # или задача принадлежит чату, в котором состоит пользователь,
    # или задача принадлежит личному списку пользователя.

    query = select(Task).distinct().outerjoin(
        chat_members, Task.chat_id == chat_members.c.chat_id
    ).outerjoin(
        TaskList, Task.task_list_id == TaskList.id
    ).where(
        (Task.created_by == user_id) |
        (Task.assigned_to == user_id) |
        (chat_members.c.user_id == user_id) |
        (TaskList.user_id == user_id) |
        ((Task.chat_id.is_(None)) & (Task.task_list_id.is_(None)) & (Task.created_by == user_id)) # Inbox
    )

    now = datetime.now(timezone.utc)

    if filter_type == "today":
        end_of_day = now.replace(hour=23, minute=59, second=59)
        query = query.where(Task.deadline != None).where(Task.deadline <= end_of_day).where(Task.status != TaskStatus.done)
    elif filter_type == "upcoming":
        seven_days_later = now + timedelta(days=7)
        query = query.where(Task.deadline != None).where(Task.deadline <= seven_days_later).where(Task.status != TaskStatus.done)
    elif filter_type == "inbox":
        # Inbox = Задачи без чата и без списка
        query = query.where(Task.chat_id.is_(None)).where(Task.task_list_id.is_(None))

    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()



async def get_list_tasks(
    db: AsyncSession,
    list_id: int,
    status_filter: Optional[TaskStatus] = None,
) -> List[Task]:
    """Получить задачи из личного списка."""
    query = select(Task).where(Task.task_list_id == list_id)
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
