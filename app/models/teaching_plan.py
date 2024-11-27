from sqlalchemy import Column, Integer, String, Date, Time
from app.database import Base

class TeachingPlan(Base):
    __tablename__ = 'teaching_plan'

    id = Column(Integer, primary_key=True, index=True)  
    teacher_code = Column(String, nullable=False)  
    start_time = Column(String, nullable=False)  
    end_time = Column(String, nullable=False)  
    date = Column(String, nullable=False)  