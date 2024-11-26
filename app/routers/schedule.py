from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.schedule_service import ScheduleService
from app.schemas import schedule_schema

router = APIRouter(prefix="/schedules", tags=["schedules"])

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
    return ScheduleService.update_schedule(db=db, shift_id=shift_id, schedule=schedule)

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
