from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Secretary(Base):
    __tablename__ = "secretaries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    office = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    user = relationship("User", back_populates="secretary")