"""
Pydantic-схемы для чатов и сообщений.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.chat import ChatType


# ── Сообщения ─────────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None  # Для ответа в ветке
    file_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    file_url: Optional[str] = None
    is_pinned: bool
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Чаты ──────────────────────────────────────────────────────

class ChatCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chat_type: ChatType = ChatType.group
    member_ids: List[int] = []


class ChatResponse(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    chat_type: ChatType
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatDetail(ChatResponse):
    """Подробная информация о чате с последними сообщениями."""
    member_count: int = 0


class ChatMemberAdd(BaseModel):
    user_ids: List[int]
