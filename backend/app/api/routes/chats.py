"""
Эндпоинты для чатов и сообщений.
"""
import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatType
from app.api.deps import get_current_admin
from app.crud.crud_chat import (
    create_chat, get_user_chats, get_chat_by_id,
    is_chat_member, create_message, get_chat_messages,
    get_thread_messages, pin_message, search_chat_messages,
    get_all_chats, delete_chat, change_chat_creator,
    get_chat_members_list, add_chat_members, remove_chat_member
)
from app.crud.crud_task import search_chat_tasks
from app.schemas.chat import (
    ChatCreate, ChatResponse, ChatDetail,
    MessageCreate, MessageResponse, ChatMemberAdd
)
from app.schemas.task import TaskResponse
from app.schemas.user import UserResponse

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


@router.get("/all", response_model=List[ChatResponse])
async def list_all_chats_admin(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Получить все чаты (только для админов)."""
    return await get_all_chats(db, skip, limit)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_admin(
    chat_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Удалить чат (только для админов)."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    await delete_chat(db, chat)


@router.put("/{chat_id}/creator", response_model=ChatResponse)
async def transfer_chat_ownership(
    chat_id: int,
    new_creator_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Передать права создателя чата другому пользователю (только для админов)."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return await change_chat_creator(db, chat, new_creator_id)


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


@router.get("/{chat_id}/members", response_model=List[UserResponse])
async def list_chat_members(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список участников чата."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await get_chat_members_list(db, chat_id)


@router.post("/{chat_id}/members", status_code=status.HTTP_200_OK)
async def add_members_to_chat(
    chat_id: int,
    members_in: ChatMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Добавить пользователей в чат (только создатель)."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if chat.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Только создатель может добавлять участников")

    await add_chat_members(db, chat_id, members_in.user_ids)
    return {"message": "Участники добавлены"}


@router.delete("/{chat_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_chat(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить пользователя из чата (только создатель)."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if chat.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Только создатель может удалять участников")
    if chat.created_by == user_id:
        raise HTTPException(status_code=400, detail="Создатель не может удалить себя. Используйте передачу прав или удалите чат.")

    await remove_chat_member(db, chat_id, user_id)


@router.delete("/{chat_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Выйти из чата."""
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=400, detail="Вы не участник этого чата")
    if chat.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="Создатель не может просто выйти. Передайте права или удалите чат.")

    await remove_chat_member(db, chat_id, current_user.id)


# ── Сообщения ─────────────────────────────────────────────────

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{chat_id}/messages/upload", response_model=MessageResponse, status_code=201)
async def upload_file_and_send_message(
    chat_id: int,
    file: UploadFile = File(...),
    content: str = Form(""),
    parent_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение с файлом."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")

    chat = await get_chat_by_id(db, chat_id)
    if chat.chat_type == ChatType.channel and chat.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="В канал может писать только его создатель")

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".doc", ".docx"}

    # Generate secure filename
    file_extension = ""
    if file.filename and "." in file.filename:
        file_extension = f".{file.filename.split('.')[-1].lower()}"

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Тип файла не поддерживается")

    secure_filename = f"{uuid.uuid4()}{file_extension}"

    file_path = os.path.join(UPLOAD_DIR, secure_filename)

    # Использование асинхронной записи
    try:
        import aiofiles
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content_chunk := await file.read(1024 * 1024):  # читаем чанками по 1MB
                await out_file.write(content_chunk)
    except ImportError:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    file_url = f"/static/uploads/{secure_filename}"

    msg_in = MessageCreate(content=content, parent_id=parent_id, file_url=file_url)
    return await create_message(db, chat_id, current_user.id, msg_in)

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


@router.get("/{chat_id}/search/messages", response_model=List[MessageResponse])
async def search_messages(
    chat_id: int,
    query: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Поиск сообщений в чате по подстроке."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await search_chat_messages(db, chat_id, query, limit)


@router.get("/{chat_id}/search/tasks", response_model=List[TaskResponse])
async def search_tasks(
    chat_id: int,
    query: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Поиск задач в чате по названию или описанию."""
    if not await is_chat_member(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Вы не участник этого чата")
    return await search_chat_tasks(db, chat_id, query, limit)
