from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas import user_schema
from fastapi import HTTPException
from passlib.context import CryptContext
from app.models.teacher import Teacher

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user(db: Session, user: user_schema.UserCreate):
        if UserService.get_user_by_email(db, user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            email=user.email,
            password=hashed_password,
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        db_teacher = Teacher(name="", subject="", phone="", user_id=db_user.id, image_path="")
        db.add(db_teacher)
        db.commit()

        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user: user_schema.UserUpdate):
        db_user = UserService.get_user(db, user_id)
        update_data = user.dict(exclude_unset=True)
        
        if 'password' in update_data:
            update_data['password'] = pwd_context.hash(update_data['password'])
            
        for key, value in update_data.items():
            setattr(db_user, key, value)
            
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = UserService.get_user(db, user_id)
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    @staticmethod
    def get_teacherid_by_email(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # if user.role != "teacher":
        #     raise HTTPException(status_code=400, detail="User is not a teacher")

        teacher = db.query(Teacher).filter(Teacher.user_id == user.id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        
        return teacher.id