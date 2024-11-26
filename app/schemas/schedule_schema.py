from typing import Optional
from pydantic import BaseModel
from datetime import date

class ScheduleBase(BaseModel):
    teacher_id: int
    description: str  
    date: str
    email: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    note: Optional[str] = None

    class Config:
        orm_mode = True

class ScheduleUpdate(BaseModel):
    teacher_id: Optional[int] = None
    description: Optional[str] = None
    date: Optional[str] = None
    note: Optional[str] = None

class Schedule(ScheduleBase):
    id: int
    note: Optional[str] = None

    class Config:
        from_attributes = True
class ScheduleResponse(ScheduleBase):
    id: int
    note: Optional[str] = None
    description: str
    date: date 

    class Config:
        orm_mode = True  
        from_attributes = True