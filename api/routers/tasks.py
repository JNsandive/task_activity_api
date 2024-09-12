from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..task_crud_impl import TaskActivityImpl
from ..models import User
from ..schemas import TaskActivityCreate, TaskResponse, TaskCreatedResponse, ResponseWrapper
from ..database import get_db
from ..auth_impl import get_current_user

router = APIRouter()
task_impl = TaskActivityImpl()


@router.post("/tasks/create", response_model=ResponseWrapper[TaskCreatedResponse])
async def create_task(task: TaskActivityCreate, db: Session = Depends(get_db),
                      current_user: int = Depends(get_current_user)):
    return await task_impl.create_task(db, task_data=task, current_user=current_user)


@router.get("/tasks/created", response_model=ResponseWrapper[List[TaskResponse]])
async def get_created_tasks(skip: int = 0, limit: int = 10,
                            sort_order: str = Query("asc", enum=["asc", "desc"]),
                            db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    return await task_impl.get_created_tasks(db, current_user=current_user, skip=skip, limit=limit,
                                             sort_order=sort_order)


@router.get("/tasks/assigned", response_model=ResponseWrapper[List[TaskResponse]])
async def get_assigned_tasks(skip: int = 0, limit: int = 10,
                             sort_order: str = Query("asc", enum=["asc", "desc"]),
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    return await task_impl.get_assigned_tasks(db, current_user=current_user, skip=skip, limit=limit,
                                              sort_order=sort_order)


@router.get("/tasks/{task_id}", response_model=ResponseWrapper[TaskResponse])
async def get_task_by_id(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await task_impl.get_task_by_id(db, task_id=task_id, current_user=current_user)


@router.put("/tasks/{task_id}", response_model=ResponseWrapper[TaskResponse])
async def update_task(task_id: int, task: TaskActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await task_impl.update_task(db, task_id=task_id, task_data=task.dict(), current_user=current_user)


@router.delete("/tasks/{task_id}")
async def delete_task_api(task_id: int, db: Session = Depends(get_db)):
    return await task_impl.delete_task(db, task_id=task_id)
