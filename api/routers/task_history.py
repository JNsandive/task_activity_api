import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..crud_impl import get_task_history, get_task_history_latest
from ..database import get_db
from ..schemas import TaskHistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tasks/{task_id}/history", response_model=list[TaskHistoryResponse])
def list_task_history(task_id: int, db: Session = Depends(get_db)):
    try:
        return get_task_history(db, task_id=task_id)
    except Exception as e:
        logger.error(f"Error fetching task history for task_id {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/tasks/{task_id}/history/latest", response_model=list[TaskHistoryResponse])
def get_latest_task_history(task_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching latest task history for task_id: {task_id}")
    try:
        return get_task_history_latest(db, task_id=task_id)
    except Exception as e:
        logger.error(f"Error fetching latest task history for task_id {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
