from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    subject = Column(String)
    phone = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    image_path = Column(String, nullable=True)
    schedules = relationship("Schedule", back_populates="teacher")
    user = relationship("User", back_populates="teacher")
    teacher_code = Column(String)
