from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.teacher_service import TeacherService
from app.services.shift_service import ShiftService 
from app.schemas import teacher_schema
from datetime import date
import os
import base64

UPLOAD_DIR = "./face_upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.get("/", response_model=List[teacher_schema.Teacher])
def get_teachers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return TeacherService.get_teachers(db, skip, limit)

@router.get("/{teacher_id}", response_model=teacher_schema.Teacher)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    return TeacherService.get_teacher(db, teacher_id)

@router.post("/", response_model=teacher_schema.Teacher)
def create_teacher(teacher: teacher_schema.TeacherCreate, db: Session = Depends(get_db)):
    return TeacherService.create_teacher(db, teacher)

@router.put("/{teacher_id}", response_model=teacher_schema.Teacher)
def update_teacher(teacher_id: int, teacher: teacher_schema.TeacherUpdate, db: Session = Depends(get_db)):
    return TeacherService.update_teacher(db, teacher_id, teacher)

@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    return TeacherService.delete_teacher(db, teacher_id)

@router.get("/shifts/{target_date}", response_model=List[dict])
def get_teachers_with_shifts(target_date: date, db: Session = Depends(get_db)):
    return ShiftService.get_teachers_with_shifts(db, target_date)
@router.get("/shifts/{target_date}/description/{description}", response_model=dict)
def get_teachers_with_shifts_by_description(
    target_date: date, description: str, db: Session = Depends(get_db)
):
    return ShiftService.get_teachers_with_shifts_by_description(db, target_date, description)
@router.post("/{teacher_id}/upload-image")
def upload_teacher_image(
    teacher_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return TeacherService.handle_image_upload(db, teacher_id, file)

@router.get("/{teacher_id}/image")
def get_teacher_image(teacher_id: int, db: Session = Depends(get_db)):
    return TeacherService.get_encoded_image(db, teacher_id)