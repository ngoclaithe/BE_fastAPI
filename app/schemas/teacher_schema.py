from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.schemas.user_schema import User
from app.schemas.dean_schema import Dean
from app.schemas.secretary_schema import Secretary
from app.schemas.schedule_schema import Schedule

class TeacherBase(BaseModel):
    name: str
    subject: str
    phone: str
    image_path: Optional[str] = None
    teacher_code: Optional[str] = None

class TeacherCreate(TeacherBase):
    user_id: Optional[int]

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[int] = None
    teacher_code: Optional[str] = None
class Teacher(TeacherBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class TeacherWithSchedules(Teacher):
    schedules: List["Schedule"] = []
    class Config:
        from_attributes = True
class UserWithDetails(User):
    dean: Optional[Dean] = None
    teacher: Optional[TeacherWithSchedules] = None
    secretary: Optional[Secretary] = None