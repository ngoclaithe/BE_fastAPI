# src/models/timetable.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Timetable(Base):
    __tablename__ = "timetables"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_code = Column(String)
    lesson = Column(String)  
    start_week = Column(Integer)  
    end_week = Column(Integer)  
    day_of_week = Column(String) 
