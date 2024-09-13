from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..task_service import TaskActivityImpl
from ..models import User
from ..schemas import TaskActivityCreate, TaskResponse, TaskCreatedResponse, ResponseWrapper
from ..database import get_db
from ..auth_impl import get_current_user

router = APIRouter()
task_impl = TaskActivityImpl()


@router.post("/tasks", response_model=ResponseWrapper[TaskCreatedResponse], tags=["Task Activity"])
async def create_task(task: TaskActivityCreate, db: Session = Depends(get_db),
                      current_user: int = Depends(get_current_user)):
    return await task_impl.create_task(db, task_data=task, current_user=current_user)


@router.get("/tasks", response_model=ResponseWrapper[List[TaskResponse]], tags=["Task Activity"])
async def get_tasks(
        task_type: str = Query("created", enum=["created", "assigned"]),
        task_name: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        due_date_from: Optional[datetime] = Query(None),
        due_date_to: Optional[datetime] = Query(None),
        activity_type_id: Optional[int] = Query(None),
        assigned_to_id: Optional[int] = Query(None),
        skip: int = 0,
        limit: int = 10,
        sort_order: str = Query("asc", enum=["asc", "desc"]),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return await task_impl.get_tasks(
        db, current_user=current_user, task_type=task_type, task_name=task_name, skip=skip, limit=limit,
        sort_order=sort_order,
        _status=status, due_date_from=due_date_from, due_date_to=due_date_to,
        activity_type_id=activity_type_id, assigned_to_id=assigned_to_id
    )


@router.get("/tasks/{task_id}", response_model=ResponseWrapper[TaskResponse], tags=["Task Activity"])
async def get_task_by_id(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await task_impl.get_task_by_id(db, task_id=task_id, current_user=current_user)


@router.put("/tasks/{task_id}", response_model=ResponseWrapper[TaskResponse], tags=["Task Activity"])
async def update_task(task_id: int, task: TaskActivityCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return await task_impl.update_task(db, task_id=task_id, task_data=task.dict(), current_user=current_user)


@router.delete("/tasks/{task_id}", response_model=ResponseWrapper, tags=["Task Activity"])
async def delete_task_api(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await task_impl.delete_task(db, task_id=task_id, current_user=current_user)
