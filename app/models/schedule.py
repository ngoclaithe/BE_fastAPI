from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    note = Column(String)

    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    shift_id = Column(Integer, ForeignKey("shifts.id"))

    teacher = relationship("Teacher", back_populates="schedules")
    shift = relationship("Shift", back_populates="schedules")