# src/utils/parseExcel.py

import pandas as pd
from sqlalchemy.orm import Session
from src.models.timetable import Timetable
from src.models.teacher import Teacher

def parse_timetable_excel(file_path: str, db: Session):
    """
    Parse excel file and save timetable data to database
    
    :param file_path: Path to the Excel file
    :param db: Database session
    :return: Number of records processed
    """
    try:

        df = pd.read_excel(file_path)
        required_columns = ['Mã CBGD', 'Tên CBGD', 'Tiết Học', 'Tuần BD', 'Tuần KT', 'Thứ']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Thiếu các cột: {missing_columns}")
        processed_records = 0
        for _, row in df.iterrows():
            teacher = db.query(Teacher).filter(
                Teacher.name == row['Tên CBGD']
            ).first()
            
            if not teacher:
                teacher = Teacher(
                    name=row['Tên CBGD']
                )
                db.add(teacher)
                db.commit()
                db.refresh(teacher)
            
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

def main(file_path: str):
    """
    Hàm chính để chạy việc parse Excel
    
    :param file_path: Đường dẫn tới file Excel
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        records = parse_timetable_excel(file_path, db)
        print(f"Đã xử lý {records} bản ghi thời khóa biểu")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main('UIS-ThoiKhoaBieu HK233.xlsx')