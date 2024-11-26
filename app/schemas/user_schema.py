# user_schema.py
from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    dean = "dean"
    teacher = "teacher"
    secretary = "secretary"

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class User(UserBase):
    id: int

    class Config:
        from_attributes = True