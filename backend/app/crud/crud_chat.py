"""
CRUD-операции для чатов и сообщений.
"""
from typing import List, Optional
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat, Message, chat_members, ChatType
from app.models.user import User
from app.schemas.chat import ChatCreate, MessageCreate


async def create_chat(
    db: AsyncSession, chat_in: ChatCreate, creator_id: int
) -> Chat:
    """Создать новый чат/группу/канал."""
    chat = Chat(
        name=chat_in.name,
        description=chat_in.description,
        chat_type=chat_in.chat_type,
        created_by=creator_id,
    )
    db.add(chat)
    await db.flush()

    # Добавляем создателя как участника (прямой INSERT в связующую таблицу)
    await db.execute(
        chat_members.insert().values(chat_id=chat.id, user_id=creator_id)
    )

    # Добавляем указанных участников
    for member_id in chat_in.member_ids:
        if member_id != creator_id:
            member = await db.get(User, member_id)
            if member:
                await db.execute(
                    chat_members.insert().values(chat_id=chat.id, user_id=member_id)
                )

    await db.commit()
    await db.refresh(chat)
    return chat


async def get_user_chats(db: AsyncSession, user_id: int) -> List[Chat]:
    """Получить все чаты пользователя."""
    result = await db.execute(
        select(Chat)
        .join(chat_members)
        .where(chat_members.c.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )
    return result.scalars().all()


async def get_chat_by_id(db: AsyncSession, chat_id: int) -> Optional[Chat]:
    """Получить чат по ID."""
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.members))
        .where(Chat.id == chat_id)
    )
    return result.scalar_one_or_none()


async def is_chat_member(db: AsyncSession, chat_id: int, user_id: int) -> bool:
    """Проверить, является ли пользователь участником чата."""
    result = await db.execute(
        select(chat_members)
        .where(chat_members.c.chat_id == chat_id)
        .where(chat_members.c.user_id == user_id)
    )
    return result.first() is not None


async def create_message(
    db: AsyncSession, chat_id: int, sender_id: int, msg_in: MessageCreate
) -> Message:
    """Отправить сообщение в чат."""
    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=msg_in.content,
        parent_id=msg_in.parent_id,
        file_url=msg_in.file_url,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_chat_messages(
    db: AsyncSession, chat_id: int, skip: int = 0, limit: int = 50
) -> List[Message]:
    """Получить сообщения чата с пагинацией."""
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_all_chats(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Chat]:
    """Получить все чаты системы (для админа)."""
    result = await db.execute(
        select(Chat).order_by(Chat.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def delete_chat(db: AsyncSession, chat: Chat) -> None:
    """Удалить чат."""
    await db.delete(chat)
    await db.commit()


async def change_chat_creator(db: AsyncSession, chat: Chat, new_creator_id: int) -> Chat:
    """Изменить владельца чата."""
    chat.created_by = new_creator_id
    await db.commit()
    await db.refresh(chat)

    # Также добавляем нового владельца в участники чата, если его там нет
    is_member = await is_chat_member(db, chat.id, new_creator_id)
    if not is_member:
        await db.execute(
            chat_members.insert().values(chat_id=chat.id, user_id=new_creator_id)
        )
        await db.commit()
        await db.refresh(chat)

    return chat


async def get_thread_messages(
    db: AsyncSession, parent_id: int
) -> List[Message]:
    """Получить ответы в ветке (thread)."""
    result = await db.execute(
        select(Message)
        .where(Message.parent_id == parent_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


async def pin_message(db: AsyncSession, message_id: int) -> Optional[Message]:
    """Закрепить/открепить сообщение."""
    msg = await db.get(Message, message_id)
    if msg:
        msg.is_pinned = not msg.is_pinned
        await db.commit()
        await db.refresh(msg)
    return msg


async def search_chat_messages(
    db: AsyncSession, chat_id: int, query: str, limit: int = 50
) -> List[Message]:
    """Поиск сообщений в чате по подстроке (без учета регистра)."""
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .where(Message.content.ilike(f"%{query}%"))
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
