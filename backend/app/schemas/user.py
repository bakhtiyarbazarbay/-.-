"""
Pydantic-схемы для пользователей и авторизации.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import RoleEnum


# ── Авторизация ──────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


# ── Пользователи ─────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_university_email(cls, v: str) -> str:
        """Проверяет, что email принадлежит университетскому домену."""
        allowed_domains = ["student.university.kz", "university.kz"]
        domain = v.split("@")[-1].lower()
        if domain not in allowed_domains:
            raise ValueError(
                f"Регистрация доступна только для домена @student.university.kz"
            )
        return v.lower()


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: RoleEnum
    is_active: bool

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: str
    password: str
