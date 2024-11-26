from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class UserRole(enum.Enum):
    dean = "dean"
    teacher = "teacher"
    secretary = "secretary"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(Enum(UserRole))
    
    dean = relationship("Dean", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)
    secretary = relationship("Secretary", back_populates="user", uselist=False)