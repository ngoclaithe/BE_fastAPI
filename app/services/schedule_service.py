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
            
        # if shift.description == "1":
        #     db_schedule.start_time = "18:00"
        #     db_schedule.end_time = "19:30"
        # elif shift.description == "2":
        #     db_schedule.start_time = "19:30"
        #     db_schedule.end_time = "21:00"
        # elif shift.description == "3":
        #     db_schedule.start_time = "21:00"
        #     db_schedule.end_time = "22:30"
        # else:
        #     raise HTTPException(status_code=400, detail="Mô tả ca làm việc không hợp lệ")

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
    ):
        db_schedule = db.query(Schedule).filter(
            Schedule.shift_id == shift_id, Schedule.teacher_id == schedule.teacher_id
        ).first()

        if not db_schedule:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy lịch làm việc cho ca làm việc này"
            )
        print("Tim thay db_schedule",db_schedule.note)
        update_data = schedule.dict(exclude_unset=True)
        print("Giá trị của update data", update_data)
        if 'note' in update_data:
            db_schedule.note = update_data['note']

        db.commit()
        db.refresh(db_schedule)

        return True

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
            start_time = "18:00"
            end_time = "19:30"
        elif shift.description == "2":
            start_time = "19:30"
            end_time = "21:00"
        elif shift.description == "3":
            start_time = "21:00"
            end_time = "22:30"
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
        end_date = start_date + timedelta(days=31)
        end_date = end_date.replace(day=1) 

        schedules = (
            db.query(Schedule)
            .join(Shift, Schedule.shift_id == Shift.id)
            .filter(Schedule.teacher_id == teacher_id)
            .filter(Shift.date >= start_date)
            .filter(Shift.date < end_date)
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
            ))

        return result
    @staticmethod
    def teacher_register_schedule(
        db: Session, teacher_id: int, description: str, date: str, note: str = "waiting"
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