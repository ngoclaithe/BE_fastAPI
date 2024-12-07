from sqlalchemy.orm import Session
from app.schemas import schedule_schema
from fastapi import HTTPException
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.teacher import Teacher
from app.models.timetable import Timetable
from app.schemas.schedule_schema import ScheduleResponse
from datetime import datetime, time, timedelta
from typing import List
from datetime import date
from app.utils.parsedata import parse_timetable_excel, check_register_schedule
from pathlib import Path
from calendar import monthrange

UPLOAD_FOLDER = Path("data_excel_upload")
UPLOAD_FILE_NAME = "upload_excel.xlsx"

class ScheduleService:
    @staticmethod
    def get_schedules(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Schedule).offset(skip).limit(limit).all()

    @staticmethod
    def get_schedule(db: Session, schedule_id: int):
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule

    @staticmethod
    def create_schedule(schedule: schedule_schema.ScheduleCreate, db: Session):
        schedule_date = datetime.strptime(schedule.date, "%Y-%m-%d").date()
        
        shifts = (
            db.query(Shift)
            .filter(Shift.description == str(schedule.description), Shift.date == schedule_date)
            .all()
        )

        if not shifts:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy ca làm việc cho mô tả và ngày đã cho"
            )

        shift = shifts[0]
        db_schedule = Schedule(
            teacher_id=schedule.teacher_id,
            shift_id=shift.id,
            note="success",
        )
        existing_schedule = db.query(Schedule).filter(
            Schedule.teacher_id == schedule.teacher_id,
            Schedule.shift_id == shift.id,  
        ).first()

        if existing_schedule:
            raise HTTPException(
                status_code=400,
                detail="Lịch làm việc của giáo viên này trong ca làm việc này đã tồn tại"
            )
            

        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        return ScheduleResponse(
            id=db_schedule.id,
            teacher_id=db_schedule.teacher_id,
            description=shift.description,
            date=shift.date,
            note=db_schedule.note
        )
    
    @staticmethod
    def update_schedule(
        db: Session, shift_id: int, schedule: schedule_schema.ScheduleUpdate
    ) -> Schedule:
        db_schedule = db.query(Schedule).filter(
            Schedule.shift_id == shift_id, Schedule.teacher_id == schedule.teacher_id
        ).first()

        if not db_schedule:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy lịch làm việc cho ca làm việc này"
            )
        print("Tim thay db_schedule", db_schedule.note)

        update_data = schedule.dict(exclude_unset=True)
        print("Giá trị của update data", update_data)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)

        db.commit()
        db.refresh(db_schedule)

        return db_schedule


    @staticmethod
    def assign_teacher_to_shift(
        db: Session, shift_id: int, teacher_id: int
    ) -> Schedule:
        shift = db.query(Shift).filter(Shift.id == shift_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()

        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        if shift.description == "1":
            start_time = "07:00"
            end_time = "11:30"
        elif shift.description == "2":
            start_time = "13:30"
            end_time = "17:00"
        elif shift.description == "3":
            start_time = "18:00"
            end_time = "20:30"
        else:
            raise HTTPException(status_code=400, detail="Invalid shift description")

        existing_schedule = (
            db.query(Schedule)
            .filter(Schedule.shift_id == shift_id, Schedule.teacher_id == teacher_id)
            .first()
        )
        if existing_schedule:
            raise HTTPException(
                status_code=400, detail="Teacher already assigned to this shift"
            )

        db_schedule = Schedule(
            teacher_id=teacher_id,
            shift_id=shift_id,
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule

    @staticmethod
    def remove_teacher_from_shift(db: Session, shift_id: int, teacher_id: int) -> bool:
        schedule = (
            db.query(Schedule)
            .filter(Schedule.shift_id == shift_id, Schedule.teacher_id == teacher_id)
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=404, detail="Teacher is not assigned to this shift"
            )

        db.delete(schedule)
        db.commit()
        return True

    @staticmethod
    def delete_schedule_by_teacher_and_description(
        db: Session, teacher_id: int, description: str, date: str
    ) -> bool:
        schedule_date = datetime.strptime(date, "%Y-%m-%d").date()
        schedules = (
            db.query(Schedule)
            .join(Shift, Schedule.shift_id == Shift.id)
            .filter(
                Schedule.teacher_id == teacher_id,
                Shift.description == description,
                Shift.date == schedule_date,
            )
            .all()
        )

        if not schedules:
            raise HTTPException(
                status_code=404,
                detail="Schedule not found for teacher, description, and date",
            )

        for schedule in schedules:
            db.delete(schedule)

        db.commit()
        return True
    @staticmethod
    def get_monthly_schedule_by_teacher(db: Session, teacher_id: int, month: str):
        start_date = datetime.strptime(month, "%Y-%m")
        print("Ngày bắt đầu:", start_date)
        _, last_day = monthrange(start_date.year, start_date.month)
        end_date = start_date.replace(day=last_day)
        print("Ngày kết:", end_date)

        schedules = (
            db.query(Schedule)
            .join(Shift, Schedule.shift_id == Shift.id)
            .filter(Schedule.teacher_id == teacher_id)
            .filter(Shift.date >= start_date.date())  
            .filter(Shift.date <= end_date.date())   
            # .filter(Schedule.note == "success") 
            .all()
        )
        
        result = []
        for schedule in schedules:
            shift = db.query(Shift).filter(Shift.id == schedule.shift_id).first()
            if not shift:
                continue  

            result.append(schedule_schema.ScheduleResponse(
                id=schedule.id,
                teacher_id=schedule.teacher_id,
                shift_id=schedule.shift_id,
                description=shift.description, 
                date=shift.date,  
                note=schedule.note,
            ))

        return result

    @staticmethod
    def teacher_register_schedule(
        db: Session, teacher_id: int, description: str, date: str, note: str = "success"
    ):

        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        shifts = db.query(Shift).filter(Shift.description == description, Shift.date == date_obj).all()

        if not shifts:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy ca làm việc cho mô tả và ngày đã cho"
            )

        shift = shifts[0]

        existing_schedule = db.query(Schedule).filter(
            Schedule.teacher_id == teacher_id,
            Schedule.shift_id == shift.id
        ).first()

        if existing_schedule:
            raise HTTPException(
                status_code=400,
                detail="Lịch làm việc của giáo viên này trong ca làm việc này đã tồn tại"
            )

        db_schedule = Schedule(
            teacher_id=teacher_id,
            shift_id=shift.id,
            note=note,
        )

        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)

        return ScheduleResponse(
            id=db_schedule.id,
            teacher_id=db_schedule.teacher_id,
            description=shift.description,
            date=shift.date,
            note=db_schedule.note
        )
    @staticmethod
    def get_today_schedules_by_teacher(db: Session, teacher_id: int):
        today = datetime.now().date()
        
        schedules = (
            db.query(Schedule)
            .join(Shift, Schedule.shift_id == Shift.id)
            .filter(
                Schedule.teacher_id == teacher_id,
                Shift.date == today,
                Schedule.note == "success"
            )
            .all()
        )
        
        result = []
        for schedule in schedules:
            shift = db.query(Shift).filter(Shift.id == schedule.shift_id).first()
            if not shift:
                continue
            
            result.append(schedule_schema.ScheduleResponse(
                id=schedule.id,
                teacher_id=schedule.teacher_id,
                description=shift.description,
                date=shift.date,
                note=schedule.note
            ))
        
        return result
    @staticmethod
    def secretary_upload_schedule(db: Session):
        try:
            file_path = UPLOAD_FOLDER / UPLOAD_FILE_NAME
            print("Đây là đường dẫn",file_path)
            parse_timetable_excel(str(file_path), db)
            check_register_schedule(db)
            return {
                "status": "success",
                "message": "Đã cập nhật yêu cầu thành công",
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")
    @staticmethod
    def change_schedule(db: Session, teacher_id: int, description: str, date: str, description_new: str, date_new: str):
        old_date = datetime.strptime(date, "%Y-%m-%d").date()
        new_date = datetime.strptime(date_new, "%Y-%m-%d").date()

        old_shift = db.query(Shift).filter(Shift.description == description, Shift.date == old_date).first()
        if not old_shift:
            raise HTTPException(status_code=404, detail="Không tìm thấy shift cũ với description và date đã cho")
        
        old_schedule = db.query(Schedule).filter(Schedule.shift_id == old_shift.id, Schedule.teacher_id == teacher_id).first()
        if old_schedule:
            db.delete(old_schedule)
            db.commit()

        new_shift = db.query(Shift).filter(Shift.description == description_new, Shift.date == new_date).first()
        if not new_shift:
            raise HTTPException(status_code=404, detail="Không tìm thấy shift mới với description và date mới đã cho")
        
        new_schedule = Schedule(
            teacher_id=teacher_id,
            shift_id=new_shift.id,
            note="waiting"
        )
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)

        return ScheduleResponse(
            id=new_schedule.id,
            teacher_id=new_schedule.teacher_id,
            description=new_shift.description,
            date=new_shift.date,
            note=new_schedule.note
        )
    @staticmethod
    def leave_schedule(db: Session, teacher_id: int, description: str, date: str):
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        shift = db.query(Shift).filter(Shift.description == description, Shift.date == date_obj).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Không tìm thấy shift với description và date đã cho")
        
        schedule = db.query(Schedule).filter(Schedule.shift_id == shift.id, Schedule.teacher_id == teacher_id).first()
        if schedule:
            schedule.note = "leave_of_absence"
            db.commit()

        return ScheduleResponse(
            id=schedule.id,
            teacher_id=schedule.teacher_id,
            description=shift.description,
            date=shift.date,
            note=schedule.note
        )
