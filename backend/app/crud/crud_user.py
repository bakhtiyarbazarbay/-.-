"""
CRUD-операции для пользователей.
"""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RoleEnum
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Получить пользователя по ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Получить пользователя по email."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Получить список пользователей."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def search_users(db: AsyncSession, query: str, limit: int = 50) -> List[User]:
    """Поиск пользователей по email или ФИО."""
    result = await db.execute(
        select(User)
        .where(
            (User.email.ilike(f"%{query}%")) | (User.full_name.ilike(f"%{query}%"))
        )
        .limit(limit)
    )
    return result.scalars().all()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Создать нового пользователя."""
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email.lower(),
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=RoleEnum.student,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Аутентификация пользователя по email и паролю."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user(
    db: AsyncSession, user: User, user_in: UserUpdate
) -> User:
    """Обновить данные пользователя."""
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    else:
        update_data.pop("password", None)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
