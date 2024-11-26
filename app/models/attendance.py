from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    check_in = Column(String, nullable=True)
    check_out = Column(String, nullable=True)
    time = Column(String, nullable=True)
    note = Column(String, nullable=True)
    result = Column(String, nullable=True)
    teacher_id = Column(Integer)
    image_checkin = Column(String, nullable=True)
    image_checkout = Column(String, nullable=True)
    date = Column(String, nullable=True)
    description = Column(String, nullable=True)
