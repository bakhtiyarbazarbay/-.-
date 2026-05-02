"""
Эндпоинты для чатов и сообщений.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatType
from app.crud.crud_chat import (
    create_chat, get_user_chats, get_chat_by_id,
    is_chat_member, create_message, get_chat_messages,
    get_thread_messages, pin_message,
)
from app.schemas.chat import (
    ChatCreate, ChatResponse, ChatDetail,
    MessageCreate, MessageResponse,
)

router = APIRouter(prefix="/chats", tags=["Чаты"])


@router.post("/", response_model=ChatResponse, status_code=201)
async def create_new_chat(
    chat_in: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новый чат / группу / канал."""
    chat = await create_chat(db, chat_in, current_user.id)
    return chat


@router.get("/", response_model=List[ChatResponse])
async def list_my_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить все чаты текущего пользователя."""
    return await get_user_chats(db, current_user.id)


@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить информацию о чате."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return ChatDetail(
        id=chat.id,
        name=chat.name,
        description=chat.description,
        chat_type=chat.chat_type,
        created_by=chat.created_by,
        created_at=chat.created_at,
        member_count=len(chat.members),
    )


# ── Сообщения ─────────────────────────────────────────────────

@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    chat_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение в чат. Поддерживает Markdown."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    # Проверка: каналы — только создатель/ассистент могут писать
    chat = await get_chat_by_id(db, chat_id)
    if chat.chat_type == ChatType.channel and chat.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="В канал может писать только его создатель")
    return await create_message(db, chat_id, current_user.id, msg_in)


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить сообщения чата (с пагинацией)."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await get_chat_messages(db, chat_id, skip, limit)


@router.get("/messages/{message_id}/thread", response_model=List[MessageResponse])
async def list_thread(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить ответы в ветке (thread)."""
    return await get_thread_messages(db, message_id)


@router.post("/messages/{message_id}/pin", response_model=MessageResponse)
async def toggle_pin(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Закрепить / открепить сообщение (доступно старосте и выше)."""
    msg = await pin_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return msg
