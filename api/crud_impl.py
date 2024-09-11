from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from .models import TaskActivity, TaskHistory, User

from datetime import datetime
import json


def create_task(db: Session, task_data, user_id: int):
    task = TaskActivity(**task_data.dict(), created_by_id=user_id, created_on=datetime.utcnow())
    db.add(task)
    db.commit()
    db.refresh(task)

    # Log task creation history
    log_task_history(db, task_id=task.task_id, action="Created", new_data=task_data.dict())

    return task


# Get tasks (ensure current_user is passed from authenticated request)
def get_tasks(db: Session, current_user: User, skip: int = 0, limit: int = 10):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Optionally, you can filter tasks created by the current user
    return db.query(TaskActivity).filter(TaskActivity.created_by_id == current_user.id).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task_data: dict):
    task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
    if task:
        # Store the previous state before the update
        previous_data = {
            "task_name": task.task_name,
            "status": task.status,
            "favorite": task.favorite
        }

        # Apply updates
        for key, value in task_data.items():
            setattr(task, key, value)
        task.modified_on = datetime.utcnow()
        db.commit()

        # Log the changes in history
        log_task_history(db, task_id=task.task_id, action="Updated", previous_data=previous_data, new_data=task_data)

        return task
    return None


def delete_task(db: Session, task_id: int):
    task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
    if task:
        # Store previous data before deletion
        previous_data = {
            "task_name": task.task_name,
            "status": task.status,
            "favorite": task.favorite
        }

        # Log task deletion in history
        log_task_history(db, task_id=task.task_id, action="Deleted", previous_data=previous_data)

        # Delete the task
        db.delete(task)
        db.commit()
    return task


def get_task_history(db: Session, task_id: int):
    return db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()


def get_task_history_latest(db: Session, task_id: int):
    return db.query(TaskHistory).filter(TaskHistory.task_id == task_id).order_by(
        desc(TaskHistory.created_at)).limit(2).all()


def log_task_history(db: Session, task_id: int, action: str, previous_data=None, new_data=None):
    # Convert data to JSON string if necessary
    history_entry = TaskHistory(
        task_id=task_id,
        action=action,
        previous_data=json.dumps(previous_data) if previous_data else None,
        new_data=json.dumps(new_data) if new_data else None,
        created_at=datetime.utcnow(),
    )
    db.add(history_entry)
    db.commit()
