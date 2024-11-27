from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from app.routers import teacher, schedule, user, shift, attendance

from app.database import engine
from app.models import teacher as teacher_model
from app.models import schedule as schedule_model
from app.models import user as user_model
from app.models import dean as dean_model
from app.models import secretary as secretary_model
from app.models import shift as shift_model
from app.models import attendance as attendance_model
from app.models import timetable as timetable_model
from app.models import teaching_plan as teaching_plan_model

user_model.Base.metadata.create_all(bind=engine)
teacher_model.Base.metadata.create_all(bind=engine)
schedule_model.Base.metadata.create_all(bind=engine)
dean_model.Base.metadata.create_all(bind=engine)
secretary_model.Base.metadata.create_all(bind=engine)
shift_model.Base.metadata.create_all(bind=engine)
attendance_model.Base.metadata.create_all(bind=engine)
timetable_model.Base.metadata.create_all(bind=engine)
teaching_plan_model.Base.metadata.create_all(bind=engine)


app = FastAPI(title="VLU API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(user.router)
app.include_router(teacher.router)
app.include_router(schedule.router)
app.include_router(shift.router)
app.include_router(attendance.router)

@app.get("/")
def read_root():
    return {"message": "VLU API"}
