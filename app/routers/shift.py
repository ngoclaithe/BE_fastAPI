from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.services.shift_service import ShiftService
from app.schemas import shift_schema

router = APIRouter(prefix="/shifts", tags=["shifts"])

@router.get("/", response_model=List[shift_schema.Shift])
def get_shifts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ShiftService.get_shifts(db, skip, limit)

@router.get("/{shift_id}", response_model=shift_schema.Shift)
def get_shift(shift_id: int, db: Session = Depends(get_db)):
    return ShiftService.get_shift(db, shift_id)

@router.get("/date/{target_date}", response_model=List[shift_schema.Shift])
def get_shifts_by_date(target_date: date, db: Session = Depends(get_db)):
    return ShiftService.get_shifts_by_date(db, target_date)

@router.get("/month/{year}/{month}", response_model=List[shift_schema.Shift])
def get_shifts_by_month_for_teacher(year: int, month: int, db: Session = Depends(get_db)):
    return ShiftService.get_shifts_by_month_for_teacher(db, year, month)

@router.get("/month-for-dean/{year}/{month}", response_model=List[shift_schema.Shift])
def get_shifts_by_month_for_dean(year: int, month: int, db: Session = Depends(get_db)):
    return ShiftService.get_shifts_by_month_for_dean(db, year, month)

@router.post("/", response_model=shift_schema.Shift)
def create_shift(shift: shift_schema.ShiftCreate, db: Session = Depends(get_db)):
    return ShiftService.create_shift(db, shift)

@router.put("/{shift_id}", response_model=shift_schema.Shift)
def update_shift(shift_id: int, shift: shift_schema.ShiftUpdate, db: Session = Depends(get_db)):
    return ShiftService.update_shift(db, shift_id, shift)

@router.put("/update_show_teacher/{year}/{month}/{show_teacher}", response_model=List[shift_schema.Shift])
def update_shift_show_teacher(year: int, month: int, show_teacher: str, db: Session = Depends(get_db)):
    return ShiftService.update_shift_show_teacher(db, year, month, show_teacher)

@router.delete("/{shift_id}")
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    return ShiftService.delete_shift(db, shift_id)
    
@router.get("/waiting/{target_date}", response_model=List[dict])
def get_teacher_waiting_shifts(target_date: date, db: Session = Depends(get_db)):
    return ShiftService.get_teacher_waiting_shifts(db, target_date)