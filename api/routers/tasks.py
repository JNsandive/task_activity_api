from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..task_crud_impl import TaskActivityImpl
from ..models import User
from ..schemas import TaskActivityCreate, TaskResponse
from ..database import get_db
from ..auth_impl import get_current_user

router = APIRouter()
task_impl = TaskActivityImpl()


@router.post("/tasks", response_model=TaskResponse)
async def create_task_api(task: TaskActivityCreate, db: Session = Depends(get_db),
                          current_user: int = Depends(get_current_user)):
    return await task_impl.create_task(db, task_data=task, user_id=current_user.id)


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)
                     ):
    return await task_impl.get_tasks(db, current_user=current_user, skip=skip, limit=limit)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_api(task_id: int, task: TaskActivityCreate, db: Session = Depends(get_db)):
    return await task_impl.update_task(db, task_id=task_id, task_data=task.dict())


@router.delete("/tasks/{task_id}")
async def delete_task_api(task_id: int, db: Session = Depends(get_db)):
    return await task_impl.delete_task(db, task_id=task_id)
