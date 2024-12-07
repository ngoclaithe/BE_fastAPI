from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from calendar import monthrange
from fastapi import HTTPException
from app.models.shift import Shift
from app.models.schedule import Schedule 
from app.models.teacher import Teacher  
from app.schemas import shift_schema
from app.models.attendance import Attendance
import calendar
from sqlalchemy import func

class ShiftService:
    @staticmethod
    def get_shifts(db: Session, skip: int = 0, limit: int = 100) -> List[Shift]:
        return db.query(Shift).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_shift_by_id(db: Session, shift_id: int) -> Optional[Shift]:
        shift = db.query(Shift).filter(Shift.id == shift_id).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        return shift
    
    @staticmethod
    def get_shifts_by_date(db: Session, target_date: date) -> List[Shift]:
        return db.query(Shift).filter(Shift.date == target_date).all()

    @staticmethod
    def get_shifts_by_month_for_teacher(db: Session, year: int, month: int) -> List[Shift]:
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        return (
            db.query(Shift)
            .filter(Shift.date >= start_date)
            .filter(Shift.date <= end_date)
            .filter(Shift.show_teacher == "true")
            .order_by(Shift.date)
            .all()
        )

    @staticmethod
    def get_shifts_by_month_for_dean(db: Session, year: int, month: int) -> List[Shift]:
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        return (
            db.query(Shift)
            .filter(Shift.date >= start_date)
            .filter(Shift.date <= end_date)
            .order_by(Shift.date)
            .all()
        )

    @staticmethod
    def create_shift(db: Session, shift: shift_schema.ShiftCreate) -> Shift:
        existing_shift = db.query(Shift).filter(Shift.date == shift.date, Shift.description == shift.description).first()
        if existing_shift:
            raise HTTPException(status_code=400, detail="Shift with this description already exists for this date")
        
        shift_data = shift.model_dump()
        shift_data["show_teacher"] = "true"
        
        db_shift = Shift(**shift_data)
        db.add(db_shift)
        db.commit()
        db.refresh(db_shift)
        return db_shift
    
    @staticmethod
    def update_shift(db: Session, shift_id: int, shift_update: shift_schema.ShiftUpdate) -> Shift:
        db_shift = ShiftService.get_shift_by_id(db, shift_id)

        for field, value in shift_update.model_dump(exclude_unset=True).items():
            setattr(db_shift, field, value)
        
        db.commit()
        db.refresh(db_shift)
        return db_shift

    @staticmethod
    def update_shift_show_teacher(db: Session, year: int, month: int, show_teacher: str) -> List[Shift]:
        shifts = db.query(Shift).filter(
            Shift.date.between(
                date(year, month, 1), 
                date(year, month, calendar.monthrange(year, month)[1])
            )
        ).all()
        for shift in shifts:
            shift.show_teacher = show_teacher
        
        db.commit()
        for shift in shifts:
            db.refresh(shift)
        
        return shifts

    @staticmethod
    def delete_shift(db: Session, shift_id: int) -> bool:
        shift = ShiftService.get_shift_by_id(db, shift_id)
        db.delete(shift)
        db.commit()
        return True

    @staticmethod
    def get_teachers_with_shifts(db: Session, target_date: date) -> List[dict]:
        shifts = db.query(Shift).filter(Shift.date == target_date).all()
        
        if not shifts:
            raise HTTPException(status_code=404, detail="No shifts found for this date")
        
        result = []
        
        for shift in shifts:
            teachers = (
                db.query(Schedule)
                .filter(Schedule.shift_id == shift.id)
                .join(Schedule.teacher) 
                .all()
            )

            teacher_data = []
            for teacher_schedule in teachers:
                teacher_data.append({
                    "teacher_id": teacher_schedule.teacher.id,  
                    "teacher_name": teacher_schedule.teacher.name, 
                    "shift_description": shift.description,
                    "start_time": teacher_schedule.start_time,  
                    "end_time": teacher_schedule.end_time,  
                })
            
            result.append({
                "shift_id": shift.id,
                "date": shift.date,
                "description": shift.description,
                "teachers": teacher_data,
            })
        
        return result
    @staticmethod
    def get_teachers_with_shifts_by_description(
        db: Session, target_date: date, description: str
    ) -> dict:
        shift = (
            db.query(Shift)
            .filter(Shift.date == target_date, Shift.description == description)
            .first()
        )
        
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found for the given date and description")
        
        teachers = (
            db.query(Schedule)
            .filter(Schedule.shift_id == shift.id, Schedule.note == "success")
            .join(Schedule.teacher)
            .all()
        )

        teacher_data = [
            {
                "teacher_id": teacher_schedule.teacher.id,
                "teacher_name": teacher_schedule.teacher.name,
                "start_time": teacher_schedule.start_time,
                "subject": teacher_schedule.teacher.subject,  
                "phone": teacher_schedule.teacher.phone,  
                "end_time": teacher_schedule.end_time,
            }
            for teacher_schedule in teachers
        ]

        return {
            "shift_id": shift.id,
            "date": shift.date,
            "description": shift.description,
            "teachers": teacher_data,
        }
    @staticmethod
    def get_teacher_waiting_shifts(db: Session, target_date: date) -> dict:

        shifts = db.query(Shift).filter(Shift.date == target_date).all()
        
        if not shifts:
            raise HTTPException(status_code=200, detail="Không có ca trực nào hôm nay")
        
        result = []
        
        for shift in shifts:
            teachers = (
                db.query(Schedule)
                .filter(Schedule.shift_id == shift.id, Schedule.note.notin_(["success", "leave_approval"]))
                .join(Schedule.teacher)
                .all()
            )
            teacher_data = [
                {
                    "teacher_id": teacher_schedule.teacher.id,
                    "teacher_name": teacher_schedule.teacher.name,
                    "start_time": teacher_schedule.start_time,
                    "subject": teacher_schedule.teacher.subject,
                    "phone": teacher_schedule.teacher.phone,
                    "end_time": teacher_schedule.end_time,
                    "note": teacher_schedule.note,
                }
                for teacher_schedule in teachers
            ]
            
            result.append({
                "shift_id": shift.id,
                "date": shift.date,
                "description": shift.description,
                "teachers": teacher_data,
            })
        
        return result

    @staticmethod
    def get_time_range(description: int):
        """
        Lấy khung giờ bắt đầu và kết thúc của ca trực dựa trên description.
        """
        time_ranges = {
            1: ("07:00:00", "11:30:00"),
            2: ("13:30:00", "17:00:00"),
            3: ("18:00:00", "20:30:00"),
        }
        return time_ranges.get(description)

    @staticmethod
    def validate_and_generate_time_referencer(db: Session, request_date: str):
        """
        Kiểm tra ngày trong request với ngày trong shift và tạo đối tượng time_referencer.
        """

        shifts = db.query(Shift).filter(Shift.date == request_date).all()
        time_referencer = []

        for shift in shifts:

            schedules = db.query(Schedule).filter(
                and_(
                    Schedule.shift_id == shift.id,
                    Schedule.note == "success"
                )
            ).all()

            for schedule in schedules:
                time_referencer.append({
                    "id_shift": shift.id,
                    "description": shift.description,
                    "teacher_id": schedule.teacher_id,
                    "date": shift.date
                })

        return time_referencer