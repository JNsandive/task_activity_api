from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud_users import create_user, get_users, get_user
from ..schemas import UserCreate, UserResponse, UserCreatedResponse, UsersResponse

router = APIRouter()


@router.post("/users", response_model=UserCreatedResponse)
def create_user_api(user_data: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_data)


@router.get("/users", response_model=list[UsersResponse])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UsersResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return get_user(db, user_id=user_id)
