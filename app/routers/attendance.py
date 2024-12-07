from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services.attendance_service import AttendanceService
from app.database import get_db
import os
import time

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"]
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AttendanceVerifyRequest(BaseModel):
    date: str
@router.post("/{teacher_id}/upload-image/check_in")
async def upload_attendance_image_check_in(
    teacher_id: int,
    file: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    API điểm danh check-in bằng nhận diện khuôn mặt
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="Không tìm thấy file ảnh"
        )

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="File không đúng định dạng. Chỉ chấp nhận .png, .jpg, .jpeg"
        )

    try:
        timestamp = int(time.time())
        file_extension = file.filename.split('.')[-1]
        filename = f"{teacher_id}.upload.{timestamp}.{file_extension}"
        filepath = os.path.join("./face_client_upload", filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        result = await AttendanceService.record_attendance(
            db=db,
            teacher_id=teacher_id,
            image_path=filepath,
            description=description,
            check_in="true" 
        )

        return {
            "status": "success",
            "data": result
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi server: {str(e)}"
        )


@router.post("/{teacher_id}/upload-image/check_out")
async def upload_attendance_image_check_out(
    teacher_id: int,
    file: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    API điểm danh check-out bằng nhận diện khuôn mặt
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="Không tìm thấy file ảnh"
        )

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="File không đúng định dạng. Chỉ chấp nhận .png, .jpg, .jpeg"
        )

    try:
        timestamp = int(time.time())  
        file_extension = file.filename.split('.')[-1]
        filename = f"{teacher_id}.upload.{timestamp}.{file_extension}"
        filepath = os.path.join("./face_client_upload", filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        result = await AttendanceService.record_attendance(
            db=db,
            teacher_id=teacher_id,
            image_path=filepath,
            description=description,
            check_out="true"  
        )

        return {
            "status": "success",
            "data": result
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi server: {str(e)}"
        )


@router.post("/verify_timing")
async def verify_attendance_timing(
    request: AttendanceVerifyRequest, 
    db: Session = Depends(get_db)
):
    """
    Endpoint để kiểm tra thời gian điểm danh của giáo viên.
    """
    try:
        result = AttendanceService.verify_attendance_timing(db, request_date=request.date)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi server: {str(e)}"
        )
@router.post("/get-attendance-details")
async def get_attendance_details(
    request: AttendanceVerifyRequest, 
    db: Session = Depends(get_db)
):
    """
    Endpoint để lấy chi tiết điểm danh theo ngày
    """
    try:
        result = AttendanceService.get_attendance_details(db, date=request.date)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi server: {str(e)}"
        )
@router.get("/get-attendance-by-teacher/{teacher_id}")
async def get_attendance_by_teacher(teacher_id: str, db: Session = Depends(get_db)):
    return AttendanceService.get_attendance_by_teacher(db, teacher_id)