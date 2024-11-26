from sqlalchemy.orm import Session
from app.models.dean import Dean
from app.schemas import dean_schema
from fastapi import HTTPException

class DeanService:
    @staticmethod
    def get_deans(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Dean).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_dean(db: Session, dean_id: int):
        dean = db.query(Dean).filter(Dean.id == dean_id).first()
        if not dean:
            raise HTTPException(status_code=404, detail="Dean not found")
        return dean
    
    @staticmethod
    def get_dean_by_user_id(db: Session, user_id: int):
        return db.query(Dean).filter(Dean.user_id == user_id).first()
    
    @staticmethod
    def create_dean(db: Session, dean: dean_schema.DeanCreate):
        # Check if user_id already has a dean profile
        if DeanService.get_dean_by_user_id(db, dean.user_id):
            raise HTTPException(status_code=400, detail="User already has a dean profile")
            
        db_dean = Dean(**dean.dict())
        db.add(db_dean)
        db.commit()
        db.refresh(db_dean)
        return db_dean
    
    @staticmethod
    def update_dean(db: Session, dean_id: int, dean: dean_schema.DeanUpdate):
        db_dean = DeanService.get_dean(db, dean_id)
        update_data = dean.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_dean, key, value)
        db.commit()
        db.refresh(db_dean)
        return db_dean
    
    @staticmethod
    def delete_dean(db: Session, dean_id: int):
        dean = DeanService.get_dean(db, dean_id)
        db.delete(dean)
        db.commit()
        return {"message": "Dean deleted successfully"}