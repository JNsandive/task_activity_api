import logging
from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .models import TaskActivity, TaskHistory, User, Attachment
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TaskActivityImpl:
    def __init__(self):
        pass

    # create a new task
    async def create_task(self, db: Session, task_data, user_id: int):
        try:
            # Create the TaskActivity
            task = TaskActivity(
                task_name=task_data.task_name,
                task_description=task_data.task_description,
                created_by_id=user_id,
                created_on=datetime.utcnow(),
                modified_on=datetime.utcnow(),
                status=task_data.status,
                favorite=task_data.favorite,
                due_date=task_data.due_date,
                action_type=task_data.action_type
            )

            db.add(task)
            db.commit()
            db.refresh(task)

            # handle the attachments, if provided
            if task_data.attachments:
                for attachment_data in task_data.attachments:
                    attachment = Attachment(
                        task_id=task.task_id,
                        file_name=attachment_data.file_name
                    )
                    db.add(attachment)
                db.commit()

            # Log task creation history
            await self.log_task_history(db, task_id=task.task_id, action="Created", new_data=task_data.dict())

            logger.info(f"Task created successfully for user {user_id}, Task ID: {task.task_id}")
            return task

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error creating task: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while creating the task")

        except Exception as e:
            logger.error(f"Unexpected error during task creation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # get all tasks
    async def get_tasks(self, db: Session, current_user: User, skip: int = 0, limit: int = 10):
        try:
            if not current_user:
                logger.warning("Unauthorized access attempt")
                raise HTTPException(status_code=401, detail="Unauthorized")

            # Optionally, you can filter tasks created by the current user
            tasks = db.query(TaskActivity).filter(TaskActivity.created_by_id == current_user.id).offset(skip).limit(
                limit).all()

            if not tasks:
                logger.info(f"No tasks found for user {current_user.id}")
                return []

            logger.info(f"Retrieved {len(tasks)} tasks for user {current_user.id}")
            return tasks

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving tasks")

        except Exception as e:
            logger.error(f"Unexpected error retrieving tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # update a task
    async def update_task(self, db: Session, task_id: int, task_data: dict):
        try:
            task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

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
            await self.log_task_history(db, task_id=task.task_id, action="Updated", previous_data=previous_data,
                                        new_data=task_data)

            logger.info(f"Task with ID {task_id} updated successfully")
            return task

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error updating task with ID {task_id}: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while updating the task")

        except Exception as e:
            logger.error(f"Unexpected error updating task with ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # delete a task
    async def delete_task(self, db: Session, task_id: int):
        try:
            task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

            # Store previous data before deletion
            previous_data = {
                "task_name": task.task_name,
                "status": task.status,
                "favorite": task.favorite
            }

            # Log task deletion in history
            await self.log_task_history(db, task_id=task.task_id, action="Deleted", previous_data=previous_data)

            # Delete the task
            db.delete(task)
            db.commit()

            logger.info(f"Task with ID {task_id} deleted successfully")
            return task

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error deleting task with ID {task_id}: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while deleting the task")

        except Exception as e:
            logger.error(f"Unexpected error deleting task with ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Task history
    async def get_task_history(self, db: Session, task_id: int):
        try:
            history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()
            if not history:
                logger.info(f"No history found for task ID {task_id}")
                return []

            logger.info(f"Retrieved history for task ID {task_id}")
            return history

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving history for task ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving task history")

        except Exception as e:
            logger.error(f"Unexpected error retrieving history for task ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Task history latest (last two records)
    async def get_task_history_latest(self, db: Session, task_id: int):
        try:
            latest_history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).order_by(
                desc(TaskHistory.created_at)).limit(2).all()
            if not latest_history:
                logger.info(f"No recent history found for task ID {task_id}")
                return []

            logger.info(f"Retrieved latest history for task ID {task_id}")
            return latest_history

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving latest history for task ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving the latest task history")

        except Exception as e:
            logger.error(f"Unexpected error retrieving latest history for task ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Log task activity history
    async def log_task_history(self, db: Session, task_id: int, action: str, previous_data=None, new_data=None):
        try:
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

            logger.info(f"Task history logged for task ID {task_id}, action: {action}")

        except HTTPException as http_exc:
            logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error logging task history for task ID {task_id}: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while logging task history")

        except Exception as e:
            logger.error(f"Unexpected error logging task history for task ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
