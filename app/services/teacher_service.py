import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.teacher import Teacher
from app.schemas import teacher_schema
import base64

UPLOAD_DIR = "./face_upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TeacherService:
    @staticmethod
    def get_teachers(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Teacher).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_teacher(db: Session, teacher_id: int):
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        return teacher
    
    @staticmethod
    def create_teacher(db: Session, teacher: teacher_schema.TeacherCreate):
        db_teacher = Teacher(**teacher.dict())
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return db_teacher
    
    @staticmethod
    def update_teacher(db: Session, teacher_id: int, teacher: teacher_schema.TeacherUpdate):
        db_teacher = TeacherService.get_teacher(db, teacher_id)
        update_data = teacher.dict(exclude_unset=True)

        for key, value in update_data.items():
            print(key, value)
            setattr(db_teacher, key, value)
        db.commit()
        db.refresh(db_teacher)
        return db_teacher
    
    @staticmethod
    def delete_teacher(db: Session, teacher_id: int):
        teacher = TeacherService.get_teacher(db, teacher_id)
        db.delete(teacher)
        db.commit()
        return {"message": "Teacher deleted successfully"}
    
    @staticmethod
    def handle_image_upload(db: Session, teacher_id: int, file: UploadFile):
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are supported.")
        teacher = TeacherService.get_teacher(db, teacher_id)
        file_extension = file.filename.split(".")[-1]
        file_name = f"{teacher_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        try:
            with open(file_path, "wb") as image_file:
                image_file.write(file.file.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")

        teacher.image_path = file_path
        db.commit()
        db.refresh(teacher)

        return {"message": "Image uploaded successfully", "image_path": file_path}
    @staticmethod
    def get_encoded_image(db: Session, teacher_id: int):
        teacher = TeacherService.get_teacher(db, teacher_id)

        if not teacher.image_path or not os.path.exists(teacher.image_path):
            raise HTTPException(status_code=404, detail="Image not found")

        try:
            with open(teacher.image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return {
                "teacher_id": teacher_id,
                "image_data": f"data:image/jpeg;base64,{encoded_string}",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error encoding image: {str(e)}")