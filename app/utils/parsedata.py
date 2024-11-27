import pandas as pd
from sqlalchemy.orm import Session
from app.models.timetable import Timetable
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.database import SessionLocal

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
                teacher_id=teacher.id,
                lesson=row['Tiết Học'],
                start_week=int(row['Tuần BD']),
                end_week=int(row['Tuần KT']),
                day_of_week=row['Thứ']
            )
            
            db.add(timetable)
            processed_records += 1
        
        db.commit()
        
        return processed_records
    
    except Exception as e:
        db.rollback()
        raise ValueError(f"Lỗi khi parse Excel: {str(e)}")
    finally:
        db.close()
