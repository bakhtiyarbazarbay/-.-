"""
Pydantic-схемы для задач (Task Manager).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.medium
    assigned_to: Optional[int] = None
    deadline: Optional[datetime] = None
    source_message_id: Optional[int] = None  # Конвертация «Сообщение → Задача»
    task_list_id: Optional[int] = None # Для создания задач в личном списке

class TaskListCreate(BaseModel):
    name: str

class TaskListResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: int
    chat_id: Optional[int] = None
    task_list_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    created_by: int
    assigned_to: Optional[int] = None
    source_message_id: Optional[int] = None
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
