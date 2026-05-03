"""
Эндпоинты для работы с профилем пользователей.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.crud.crud_user import get_users, get_user_by_id, update_user, search_users
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Получить профиль текущего пользователя."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить профиль текущего пользователя."""
    # Обычный пользователь не может менять свою роль
    if user_in.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя изменить собственную роль",
        )
    return await update_user(db, current_user, user_in)


@router.get("/search", response_model=List[UserResponse])
async def search_for_users(
    query: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Поиск пользователей по email или ФИО (доступно всем авторизованным пользователям)."""
    return await search_users(db, query, limit=limit)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Получить список всех пользователей (только для админов)."""
    return await get_users(db, skip=skip, limit=limit)


@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Изменить роль пользователя (только для админов)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await update_user(db, user, user_in)
