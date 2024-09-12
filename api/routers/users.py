from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud_users import UserImpl
from ..schemas import UserCreate, UserResponse, UserCreatedResponse, UsersResponse

router = APIRouter()
user_impl = UserImpl()


@router.post("/users", response_model=UserCreatedResponse, tags=["User Activity"])
async def create_user_api(user_data: UserCreate, db: Session = Depends(get_db)):
    return await user_impl.create_user(db, user_data)


@router.get("/users", response_model=list[UsersResponse], tags=["User Activity"])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return await user_impl.get_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UsersResponse, tags=["User Activity"])
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return await  user_impl.get_user(db, user_id=user_id)
