import pandas as pd
from sqlalchemy.orm import Session
from app.models.timetable import Timetable
from app.models.teaching_plan import TeachingPlan
from app.models.teacher import Teacher
from app.models.schedule import Schedule
from app.models.shift import Shift
from datetime import datetime
from app.database import SessionLocal

shift_times = {
    "1": ("07:00", "11:30"),
    "2": ("13:30", "17:00"),
    "3": ("18:00", "20:30")
}

lesson_times = {
    1: ("07:00", "07:50"),
    2: ("07:50", "08:40"),
    3: ("08:40", "09:30"),
    4: ("09:30", "10:20"),
    5: ("10:20", "11:10"),
    6: ("11:10", "12:00"),
    7: ("13:00", "13:50"),
    8: ("13:50", "14:40"),
    9: ("14:40", "15:30"),
    10: ("15:30", "16:20"),
    11: ("16:20", "17:10"),
    12: ("17:10", "18:00"),
    13: ("18:00", "18:50"),
    14: ("18:50", "19:40"),
    15: ("19:40", "20:30"),
    16: ("20:30", "21:20"),    
}

def parse_timetable_excel(file_path: str, db: Session):
    try:
        df = pd.read_excel(file_path)
        required_columns = ['Mã CBGD', 'Tên CBGD', 'Tiết Học', 'Tuần BD', 'Tuần KT', 'Thứ']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Thiếu các cột: {missing_columns}")

        processed_records = 0
        for _, row in df.iterrows():
            timetable = Timetable(
                teacher_code=row['Mã CBGD'],
                lesson=row['Tiết Học'],
                start_week=int(row['Tuần BD']),
                end_week=int(row['Tuần KT']),
                day_of_week=row['Thứ']
            )
            db.add(timetable)
            db.commit()  

            start_lesson = row['Tiết Học']  
            end_lesson = start_lesson 

            if isinstance(start_lesson, str) and '-' in start_lesson:
                start_lesson, end_lesson = start_lesson.split('-')
                start_lesson = int(start_lesson.strip())  
                end_lesson = int(end_lesson.strip())  
            else:
                start_lesson = int(start_lesson)  

            start_time, _ = lesson_times.get(start_lesson, (None, None))
            _, end_time = lesson_times.get(end_lesson, (None, None))

            if start_time is None or end_time is None:
                print(f"Không tìm thấy giờ học cho tiết {start_lesson}-{end_lesson} của giáo viên {row['Mã CBGD']}")
                continue  

            base_date = pd.to_datetime("2024-09-02")  
            day_offset = {"Thứ 2": 0, "Thứ 3": 1, "Thứ 4": 2, "Thứ 5": 3, "Thứ 6": 4, "Thứ 7": 5, "Chủ nhật": 6}
            day_of_week_offset = day_offset.get(row['Thứ'], 0)

            start_date = base_date + pd.DateOffset(weeks=timetable.start_week - 1, days=day_of_week_offset)

            teaching_plan = TeachingPlan(
                teacher_code=row['Mã CBGD'],  
                start_time=start_time,  
                end_time=end_time,  
                date=start_date.date() 
            )
            db.add(teaching_plan)
            processed_records += 1
            db.commit()

        return processed_records

    except Exception as e:
        db.rollback()
        raise ValueError(f"Lỗi khi parse Excel: {str(e)}")
    finally:
        db.close()


def check_register_schedule(db: Session):
    schedules_with_details = (
        db.query(
            Schedule.id.label("schedule_id"),
            Schedule.note,
            Schedule.shift_id,
            Schedule.teacher_id,
            Teacher.teacher_code,
            Shift.date.label("shift_date"),
            Shift.description.label("shift_description"),
            TeachingPlan.start_time.label("plan_start_time"),
            TeachingPlan.end_time.label("plan_end_time"),
        )
        .join(Teacher, Teacher.id == Schedule.teacher_id)
        .join(Shift, Shift.id == Schedule.shift_id)
        .outerjoin(
            TeachingPlan,
            (TeachingPlan.teacher_code == Teacher.teacher_code)
            & (TeachingPlan.date == Shift.date),  
        )
        # .filter(Schedule.note == "success")
        .all()
    )

    for schedule in schedules_with_details:
        print(f"Tồn tại ca trực {schedule.shift_description} và {schedule.plan_start_time} và {schedule.plan_end_time} của {schedule.schedule_id}")

        start_time_str, end_time_str = shift_times[schedule.shift_description]
        shift_start_time = datetime.strptime(
            f"{schedule.shift_date} {start_time_str}", "%Y-%m-%d %H:%M"
        )
        shift_end_time = datetime.strptime(
            f"{schedule.shift_date} {end_time_str}", "%Y-%m-%d %H:%M"
        )

        if schedule.plan_start_time and schedule.plan_end_time:
            plan_start_time = datetime.strptime(
                f"{schedule.shift_date} {schedule.plan_start_time}", "%Y-%m-%d %H:%M"
            )
            plan_end_time = datetime.strptime(
                f"{schedule.shift_date} {schedule.plan_end_time}", "%Y-%m-%d %H:%M"
            )
            print(f"Thời gian ca trực bắt đầu {shift_start_time} và thời gian kết thúc lịch dạy {plan_end_time}")
            if not (shift_end_time <= plan_start_time or shift_start_time >= plan_end_time):
                db.query(Schedule).filter(Schedule.id == schedule.schedule_id).update(
                    {"note": "fail"}
                )
                db.commit()
                continue

        db.query(Schedule).filter(Schedule.id == schedule.schedule_id).update(
            {"note": "success"}
        )
        db.commit()