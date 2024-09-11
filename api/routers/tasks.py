from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..crud_impl import create_task, get_tasks, update_task, delete_task
from ..models import User
from ..schemas import TaskCreate, TaskResponse
from ..database import get_db
from ..auth_impl import get_current_user

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse)
def create_task_api(task: TaskCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    return create_task(db, task_data=task, user_id=current_user.id)


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # User must be authenticated
):
    return get_tasks(db, current_user=current_user, skip=skip, limit=limit)



@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task_api(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    return update_task(db, task_id=task_id, task_data=task.dict())


@router.delete("/tasks/{task_id}")
def delete_task_api(task_id: int, db: Session = Depends(get_db)):
    return delete_task(db, task_id=task_id)
