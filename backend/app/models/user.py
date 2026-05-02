from sqlalchemy import Column, Integer, String, Boolean, Enum
import enum
from app.database import Base

class RoleEnum(str, enum.Enum):
    student = "student"
    starosta = "starosta"
    assistant = "assistant"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.student)
    is_active = Column(Boolean, default=True)
