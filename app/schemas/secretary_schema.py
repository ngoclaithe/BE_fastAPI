from typing import Optional
from pydantic import BaseModel

class SecretaryBase(BaseModel):
    name: str
    phone: str
    office: str

class SecretaryCreate(SecretaryBase):
    user_id: int

class SecretaryUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    office: Optional[str] = None

class Secretary(SecretaryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True