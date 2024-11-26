from typing import Optional
from pydantic import BaseModel

class DeanBase(BaseModel):
    name: str
    phone: str
    department: str

class DeanCreate(DeanBase):
    user_id: int

class DeanUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None

class Dean(DeanBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True