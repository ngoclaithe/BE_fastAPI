from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.attendance import Attendance
from app.models.teacher import Teacher 
from app.models.schedule import Schedule 
from app.models.shift import Shift 
from datetime import datetime
import face_recognition
import os

UPLOAD_FOLDER = './face_upload'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_faces_in_folder(db: Session):
    """
    Mã hóa khuôn mặt từ các file ảnh trong thư mục upload và ánh xạ ID của giáo viên
    với ID của giáo viên trong cơ sở dữ liệu.
    """
    known_faces = []
    image_filenames = []
    teacher_id_map = {}  
    teachers = db.query(Teacher).all()
    for teacher in teachers:
        teacher_id_map[teacher.id] = teacher.id  

    for filename in os.listdir(UPLOAD_FOLDER):
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            img = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(img)

            if face_encodings:
                known_faces.append(face_encodings[0])
                image_filenames.append(filename)
                
                teacher_id_reference = filename.split('.')[0]  
                print(f"Processing file: {filename}, Teacher ID reference: {teacher_id_reference}")

                if int(teacher_id_reference) not in teacher_id_map:
                    raise HTTPException(status_code=400, detail=f"Không tìm thấy giáo viên với ID {teacher_id_reference}")
        except Exception as e:
            continue

    return known_faces, image_filenames, teacher_id_map


class AttendanceService:
    @staticmethod
    async def record_attendance(
        db: Session, 
        teacher_id: int, 
        image_path: str,  
        check_in: str = None,
        check_out: str = None,
        description: str = None,
    ):
        """
        Ghi nhận điểm danh của giáo viên dựa trên việc nhận diện khuôn mặt trong ảnh.
        """
        try:
            known_faces, image_filenames, teacher_id_map = encode_faces_in_folder(db)
          
            img = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(img)
            face_encodings = face_recognition.face_encodings(img, face_locations)
          
            if not face_encodings:
                raise HTTPException(
                    status_code=400,
                    detail="Không tìm thấy khuôn mặt trong ảnh"
                )
            
            matched_faces = []
            face_confidences = []
            matched_teacher_ids = []  

            for encoding in face_encodings:
                distances = face_recognition.face_distance(known_faces, encoding)
                best_match_index = distances.argmin()
                best_match_distance = distances[best_match_index]
                print(best_match_distance)
                  
                if best_match_distance < 0.2:  
                    
                    matched_faces.append(image_filenames[best_match_index])

                    face_confidences.append(1 - best_match_distance)
                    matched_teacher_id = int(image_filenames[best_match_index].split('.')[0])
                    matched_teacher_ids.append(matched_teacher_id)
                    
                    print(f"ID khớp với ảnh là : {matched_teacher_id}")  

            if not matched_faces:
                raise HTTPException(
                    status_code=400,
                    detail="Không nhận diện được khuôn mặt từ ảnh"
                )

            current_date = datetime.now().date()
            time_check = datetime.now().strftime("%H:%M:%S")
            filename = os.path.basename(image_path)
            teacher_id_upload = filename.split('.')[0]

            print(f"Uploaded image teacher ID: {teacher_id_upload}")

            if str(teacher_id) != teacher_id_upload:
                raise HTTPException(
                    status_code=400,
                    detail="Tên giáo viên không khớp với ảnh"
                )

            attendance_record = Attendance(
                teacher_id=teacher_id,
                date=str(current_date),
                check_in=check_in,
                check_out=check_out,
                image_checkin=image_path if check_in else None,
                image_checkout=image_path if check_out else None,
                time = str(time_check),
                description=description,
            )

            db.add(attendance_record)
            db.commit()
            db.refresh(attendance_record)

            return {
                "success": True,
                "message": "Điểm danh thành công",
                "attendance_id": attendance_record.id,
                "matched_faces": matched_faces,  
                "face_confidences": face_confidences  
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi xử lý điểm danh: {str(e)}"
            )
    @staticmethod
    def verify_attendance_timing(db: Session, request_date: str):
        """
        Kiểm tra thời gian điểm danh của giáo viên so với thời gian ca trực.
        Cập nhật ghi chú trong attendance cho biết giáo viên đi muộn hoặc về sớm bao nhiêu phút.
        """
        try:
            shifts = db.query(Shift).filter(Shift.date == request_date).all()
            if not shifts:
                raise HTTPException(status_code=404, detail="Không tìm thấy ca trực cho ngày này")

            description_to_times = {
                '1': ('18:00:00', '19:30:00'),
                '2': ('19:30:00', '21:00:00'),
                '3': ('21:00:00', '22:30:00'),
            }

            time_referencers = []
            for shift in shifts:
                teacher_ids = (
                    db.query(Schedule.teacher_id)
                    .filter(Schedule.shift_id == shift.id, Schedule.note == 'success')
                    .all()
                )
                teacher_ids = [teacher_id[0] for teacher_id in teacher_ids]
                for teacher_id in teacher_ids:
                    start_time, end_time = description_to_times.get(str(shift.description), (None, None))
                    if start_time and end_time:
                        time_referencers.append({
                            "id_shift": shift.id,
                            "description": shift.description,
                            "teacher_id": teacher_id,
                            "date": shift.date,
                            "start_time": start_time,
                            "end_time": end_time,
                        })

            for ref in time_referencers:
                attendances = (
                    db.query(Attendance)
                    .filter(
                        Attendance.teacher_id == ref["teacher_id"],
                        Attendance.date == ref["date"],
                        Attendance.description == ref["description"],
                    )
                    .all()
                )
                for attendance in attendances:

                    check_time = datetime.strptime(attendance.time, "%H:%M:%S") if attendance.time else None

                    note = []
                    if attendance.check_in:
                        if check_time and check_time > datetime.strptime(ref["start_time"], "%H:%M:%S"):
                            diff_minutes = int((check_time - datetime.strptime(ref["start_time"], "%H:%M:%S")).total_seconds() / 60)
                            note.append(f"Đi muộn {diff_minutes} phút")
                    if attendance.check_out:
                        if check_time and check_time < datetime.strptime(ref["end_time"], "%H:%M:%S"):
                            diff_minutes = int((datetime.strptime(ref["end_time"], "%H:%M:%S") - check_time).total_seconds() / 60)
                            note.append(f"Về sớm {diff_minutes} phút")

                    attendance.note = ", ".join(note) if note else "Đúng giờ"
                    db.add(attendance)

            db.commit()

            return {"success": True, "message": "Kiểm tra thời gian điểm danh hoàn tất"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi kiểm tra thời gian điểm danh: {str(e)}"
            )
    @staticmethod
    def get_attendance_details(db: Session, date: str):
        """
        Trả về chi tiết điểm danh của tất cả giáo viên theo ngày và ca trực
        
        Args:
            db (Session): Database session
            date (str): Ngày điểm danh (format: 'YYYY-MM-DD')
        
        Returns:
            Chi tiết điểm danh bao gồm cả giáo viên đã và chưa điểm danh
        """
        try:
            shifts = db.query(Shift).filter(Shift.date == date).all()
            
            attendance_details = []
            
            for shift in shifts:
                scheduled_teachers = (
                    db.query(Schedule.teacher_id, Teacher)
                    .join(Teacher, Schedule.teacher_id == Teacher.id)
                    .filter(
                        Schedule.shift_id == shift.id, 
                        Schedule.note == 'success'
                    )
                    .all()
                )
                
                for teacher_id, teacher in scheduled_teachers:
                    attendance = (
                        db.query(Attendance)
                        .filter(
                            Attendance.teacher_id == teacher_id,
                            Attendance.date == date,
                            Attendance.description == str(shift.description)
                        )
                        .first()
                    )
                    
                    detail = {
                        "shift_description": shift.description,
                        "date": date,
                        "teacher_name": teacher.name,
                        "teacher_id": teacher.id,
                        "time_check_in": attendance.time if attendance and attendance.check_in else None,
                        "time_check_out": attendance.time if attendance and attendance.check_out else None,
                        "note_check_in": attendance.note.split(", ")[0] if attendance and attendance.note and "muộn" in attendance.note else "Đúng giờ" if attendance else "Chưa điểm danh",
                        "note_check_out": attendance.note.split(", ")[1] if attendance and attendance.note and "về sớm" in attendance.note else "Đúng giờ" if attendance else "Chưa điểm danh",
                        "attendance_status": "Đã điểm danh" if attendance else "Chưa điểm danh",
                        "image_path_checkin": attendance.image_checkin if attendance else None,
                        "image_path_checkout": attendance.image_checkout if attendance else None
                    }
                    
                    attendance_details.append(detail)
            
            return {
                "success": True,
                "attendance_details": attendance_details
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi truy xuất chi tiết điểm danh: {str(e)}"
            )