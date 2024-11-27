from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class ShiftBase(BaseModel):
    date: date
    description: Optional[str] = None
    show_teacher: Optional[str] = None
class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(ShiftBase):
    pass

class Shift(ShiftBase):
    id: int
    
    class Config:
        from_attributes = True