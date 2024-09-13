import logging
from typing import List

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session, Query

from ..task_history_service import TasksHistory
from ..database import get_db
from ..schemas import TaskHistoryResponse, TaskHistoryDetailsResponse, ResponseWrapper

router = APIRouter()
logger = logging.getLogger(__name__)
task_history = TasksHistory()


@router.get("/tasks/history/", response_model=ResponseWrapper[List[TaskHistoryResponse]], tags=["Task History"])
async def get_all_task_histories(skip: int = 0, limit: int = 10, sort_order: str = "asc",
                                 db: Session = Depends(get_db)):
    return await task_history.get_all_task_histories(db, skip=skip, limit=limit, sort_order=sort_order)


@router.get("/tasks/{task_id}/history_details", response_model=ResponseWrapper[TaskHistoryDetailsResponse],
            tags=["Task History"])
async def get_task_history_details(task_id: int, db: Session = Depends(get_db)):
    return await task_history.get_task_history_details(task_id=task_id, db=db)
