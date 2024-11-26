from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.database import get_db
from app.services.user_service import UserService
from app.schemas import user_schema
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users"])

SECRET_KEY = "my-secret-key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = UserService.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=user_schema.User)
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    return UserService.create_user(db=db, user=user)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = UserService.get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    print({"access_token": access_token, "token_type": "bearer"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=user_schema.User)
def read_users_me(current_user: user_schema.User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[user_schema.User])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: user_schema.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("Current user role:", current_user.role)
    if current_user.role.value != "dean":  
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return UserService.get_users(db, skip=skip, limit=limit)

@router.put("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: user_schema.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not pwd_context.verify(old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    user_update = user_schema.UserUpdate(password=new_password)
    updated_user = UserService.update_user(db, current_user.id, user_update)
    return {"message": "Password updated successfully"}

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: user_schema.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "dean" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return UserService.delete_user(db, user_id)

@router.put("/{user_id}", response_model=user_schema.User)
def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    current_user: user_schema.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if current_user.role.value != "dean" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return UserService.update_user(db, user_id, user_update)
@router.get("/teacher-id/{email}", response_model=int)
def get_teacher_id_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):

    # if current_user.role.value != "teacher":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )

    teacher_id = UserService.get_teacherid_by_email(db, email)
    return teacher_id