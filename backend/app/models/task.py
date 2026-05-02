"""
Модели для системы управления задачами: Канбан-доски, задачи.
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    todo = "todo"               # К выполнению
    in_progress = "in_progress" # В процессе
    done = "done"               # Выполнено


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Task(Base):
    """Задача, привязанная к конкретному чату."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium, nullable=False)

    # Кто создал и кому назначено
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Конвертация из сообщения
    source_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # Дедлайн
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    chat = relationship("Chat", back_populates="tasks")
    creator = relationship("User", foreign_keys=[created_by], backref="created_tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], backref="assigned_tasks")
    source_message = relationship("Message", backref="task")
