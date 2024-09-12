import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..task_crud_impl import TaskActivityImpl
from ..database import get_db
from ..schemas import TaskHistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)
task_activity_impl = TaskActivityImpl()


@router.get("/tasks/{task_id}/history", response_model=list[TaskHistoryResponse],tags=["Task History"])
def list_task_history(task_id: int, db: Session = Depends(get_db)):
    return task_activity_impl.get_task_history(db, task_id=task_id)


@router.get("/tasks/{task_id}/history/latest", response_model=list[TaskHistoryResponse],tags=["Task History"])
def get_latest_task_history(task_id: int, db: Session = Depends(get_db)):
    return task_activity_impl.get_task_history_latest(db, task_id=task_id)
