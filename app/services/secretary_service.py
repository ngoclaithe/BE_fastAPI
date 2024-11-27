from sqlalchemy.orm import Session
from app.models.secretary import Secretary
from app.schemas import secretary_schema
from fastapi import HTTPException

class SecretaryService:
    @staticmethod
    def get_secretaries(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Secretary).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_secretary(db: Session, secretary_id: int):
        secretary = db.query(Secretary).filter(Secretary.id == secretary_id).first()
        if not secretary:
            raise HTTPException(status_code=404, detail="Secretary not found")
        return secretary
    
    @staticmethod
    def get_secretary_by_user_id(db: Session, user_id: int):
        return db.query(Secretary).filter(Secretary.user_id == user_id).first()
    
    @staticmethod
    def create_secretary(db: Session, secretary: secretary_schema.SecretaryCreate):
        if SecretaryService.get_secretary_by_user_id(db, secretary.user_id):
            raise HTTPException(status_code=400, detail="User already has a secretary profile")
            
        db_secretary = Secretary(**secretary.dict())
        db.add(db_secretary)
        db.commit()
        db.refresh(db_secretary)
        return db_secretary
    
    @staticmethod
    def update_secretary(db: Session, secretary_id: int, secretary: secretary_schema.SecretaryUpdate):
        db_secretary = SecretaryService.get_secretary(db, secretary_id)
        update_data = secretary.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_secretary, key, value)
        db.commit()
        db.refresh(db_secretary)
        return db_secretary
    
    @staticmethod
    def delete_secretary(db: Session, secretary_id: int):
        secretary = SecretaryService.get_secretary(db, secretary_id)
        db.delete(secretary)
        db.commit()
        return {"message": "Secretary deleted successfully"}