from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.schedule_service import ScheduleService
from app.schemas import schedule_schema
from pathlib import Path
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])
UPLOAD_FOLDER = Path("data_excel_upload")
UPLOAD_FILE_NAME = "upload_excel.xlsx"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=List[schedule_schema.Schedule])
def get_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ScheduleService.get_schedules(db, skip, limit)

@router.get("/{schedule_id}", response_model=schedule_schema.Schedule)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    return ScheduleService.get_schedule(db, schedule_id)

@router.get("/monthly/{teacher_id}/{month}", response_model=List[schedule_schema.ScheduleResponse])
def get_monthly_schedule(
    teacher_id: int, 
    month: str, 
    db: Session = Depends(get_db)
):
    return ScheduleService.get_monthly_schedule_by_teacher(db=db, teacher_id=teacher_id, month=month)

@router.post("/register", response_model=schedule_schema.ScheduleResponse)
def create_schedule(schedule: schedule_schema.ScheduleCreate, db: Session = Depends(get_db)):
    return ScheduleService.create_schedule(db=db, schedule=schedule)

@router.put("/{shift_id}", response_model=schedule_schema.Schedule)
def update_schedule(shift_id: int, schedule: schedule_schema.ScheduleUpdate, db: Session = Depends(get_db)):
    print("Gia tri shift id", shift_id)
    print("Gia tri schedule", schedule)
    updated_schedule = ScheduleService.update_schedule(db=db, shift_id=shift_id, schedule=schedule)
    return updated_schedule

@router.put("/change_by_teacher/{teacher_id}/{description}/{date}/{description_new}/{date_new}", response_model=schedule_schema.ScheduleResponse)
def change_schedule_endpoint(
    teacher_id: int, description: str, date: str, description_new: str, date_new: str, db: Session = Depends(get_db)
):
    try:
        updated_schedule = ScheduleService.change_schedule(
            db=db,
            teacher_id=teacher_id,
            description=description,
            date=date,
            description_new=description_new,
            date_new=date_new
        )
        
        return updated_schedule

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi không mong muốn khi thay đổi lịch: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi thay đổi lịch")
@router.put("/leave_by_teacher/{teacher_id}/{description}/{date}", response_model=schedule_schema.ScheduleResponse)
def leave_schedule_endpoint(
    teacher_id: int, description: str, date: str, db: Session = Depends(get_db)
):
    try:
        updated_schedule = ScheduleService.leave_schedule(
            db=db,
            teacher_id=teacher_id,
            description=description,
            date=date,
        )
        
        return updated_schedule

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi không mong muốn khi thay đổi lịch: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi thay đổi lịch")


@router.post("/assign/{shift_id}/{teacher_id}", response_model=schedule_schema.Schedule)
def assign_teacher_to_shift(shift_id: int, teacher_id: int, db: Session = Depends(get_db)):
    return ScheduleService.assign_teacher_to_shift(db=db, shift_id=shift_id, teacher_id=teacher_id)

@router.delete("/remove/{shift_id}/{teacher_id}")
def remove_teacher_from_shift(shift_id: int, teacher_id: int, db: Session = Depends(get_db)):
    return ScheduleService.remove_teacher_from_shift(db=db, shift_id=shift_id, teacher_id=teacher_id)

@router.delete("/remove_by_teacher/{teacher_id}/{description}/{date}")
def remove_schedule_by_teacher_and_description(
    teacher_id: int, 
    description: str, 
    date: str, 
    db: Session = Depends(get_db)
):
    return ScheduleService.delete_schedule_by_teacher_and_description(
        db=db,
        teacher_id=teacher_id,
        description=description,
        date=date
    )

@router.post("/teacher_register_schedule", response_model=schedule_schema.ScheduleResponse)
def teacher_register_schedule(
    schedule: schedule_schema.ScheduleCreate,
    db: Session = Depends(get_db)
):
    return ScheduleService.teacher_register_schedule(
        db=db, 
        teacher_id=schedule.teacher_id, 
        description=schedule.description, 
        date=schedule.date, 
        note=schedule.note
    )
@router.get("/today/{teacher_id}", response_model=List[schedule_schema.ScheduleResponse])
def get_today_schedules(teacher_id: int, db: Session = Depends(get_db)):
    return ScheduleService.get_today_schedules_by_teacher(db=db, teacher_id=teacher_id)

@router.post("/secretary_upload_schedule")
async def secretary_upload_schedule(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:

        if not file.filename:
            raise HTTPException(status_code=400, detail="Không có file được chọn")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Loại file không hợp lệ. Vui lòng tải lên tệp Excel")

        logger.info(f"Uploading file: {file.filename}")

        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
        existing_file_path = UPLOAD_FOLDER / UPLOAD_FILE_NAME

        if existing_file_path.exists():
            existing_file_path.unlink()

        try:
            with open(existing_file_path, "wb") as f:
                while content := await file.read(1024 * 1024): 
                    f.write(content)
            
            logger.info(f"File saved successfully at {existing_file_path}")

            file_size = existing_file_path.stat().st_size
            logger.info(f"File size: {file_size} bytes")

            if file_size == 0:
                raise ValueError("File tải lên rỗng")

        except Exception as save_error:
            logger.error(f"Lỗi khi lưu file: {save_error}")
            raise HTTPException(status_code=500, detail=f"Không thể lưu file: {str(save_error)}")

        try:
            logger.info("Bắt đầu xử lý file lịch")
            # result = "OK"
            result = ScheduleService.secretary_upload_schedule(
                db=db,
            )
            logger.info(f"Xử lý file thành công. Số bản ghi: {len(result) if result else 0}")
        
        except Exception as process_error:
            logger.error(f"Lỗi khi xử lý file: {process_error}")

            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(process_error)}")
        
        return {
            "status": "success",
            "message": "Tải file và xử lý thành công",
            "total_records": len(result) if result else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:

        logger.error(f"Lỗi không mong muốn: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi xử lý file")