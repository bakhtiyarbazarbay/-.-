"""
Модели для системы коммуникаций: чаты, сообщения, ветки (threads).
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ChatType(str, enum.Enum):
    personal = "personal"       # Личные сообщения (1-на-1)
    group = "group"             # Группы (до 200 чел.)
    channel = "channel"         # Каналы (Read-only, публикации)


# Таблица связи участников чатов (many-to-many)
chat_members = Table(
    "chat_members",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
)


class Chat(Base):
    """Чат / Группа / Канал."""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)          # null для личных чатов
    description = Column(Text, nullable=True)
    chat_type = Column(Enum(ChatType), default=ChatType.group, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    members = relationship("User", secondary=chat_members, backref="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    """Сообщение в чате."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)              # Поддержка Markdown
    is_pinned = Column(Boolean, default=False)          # Закрепление постов
    parent_id = Column(Integer, ForeignKey("messages.id"), nullable=True)  # Для веток (threads)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", backref="messages")
    replies = relationship("Message", backref="parent", remote_side=[id])
