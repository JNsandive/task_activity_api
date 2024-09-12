import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi.responses import JSONResponse
from fastapi import HTTPException, status

from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import TaskActivity, TaskHistory, User, Attachment, ActivityType, ActivityGroup, Stage, CoreGroup
from datetime import datetime
import json

from .schemas import TaskResponse, ResponseWrapper, TaskCreatedResponse

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def validate_core_group(db: Session, core_group_id: int):
    core_group = db.query(CoreGroup).filter(CoreGroup.id == core_group_id).first()
    if not core_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Core group with id {core_group_id} does not exist."
        )
    return core_group


def validate_activity_type(db: Session, activity_type_id: int):
    activity_type = db.query(ActivityType).filter(ActivityType.id == activity_type_id).first()
    if not activity_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activity type with id {activity_type_id} does not exist."
        )
    return activity_type


def validate_assign_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id {user_id} does not exist to assign."
        )
    return user


def validate_stage(db: Session, stage_id: int):
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stage with id {stage_id} does not exist."
        )
    return stage


def validate_activity_group(db: Session, activity_group_id: int):
    activity_group = db.query(ActivityGroup).filter(ActivityGroup.id == activity_group_id).first()
    if not activity_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activity group with id {activity_group_id} does not exist."
        )
    return activity_group


# Validate due date
def validate_due_date(due_date: datetime):
    if due_date and due_date <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The due date must be a future date."
        )
    else:
        return True


# Validate fields asynchronously using a ThreadPoolExecutor
def run_validations(db: Session, task_data):
    with ThreadPoolExecutor() as executor:
        validation_tasks = [executor.submit(validate_activity_type, db, task_data.activity_type_id)]

        if task_data.activity_group_id:
            validation_tasks.append(
                executor.submit(validate_activity_group, db, task_data.activity_group_id))

        if task_data.stage_id:
            validation_tasks.append(executor.submit(validate_stage, db, task_data.stage_id))

        if task_data.core_group_id:
            validation_tasks.append(executor.submit(validate_core_group, db, task_data.core_group_id))

        if task_data.assigned_to_id:
            validation_tasks.append(executor.submit(validate_assign_user, db, task_data.assigned_to_id))

        # Collect the results
        for future in validation_tasks:
            future.result()  # Raise any exceptions from the validation


# Create a task entry in the database
def _create_task_entry(db: Session, task_data, user_id: int):
    task = TaskActivity(
        task_name=task_data.task_name,
        task_description=task_data.task_description,
        created_by_id=user_id,
        created_on=datetime.utcnow(),
        modified_on=datetime.utcnow(),
        status=task_data.status,
        favorite=task_data.favorite,
        due_date=task_data.due_date,
        action_type=task_data.action_type,
        activity_type_id=task_data.activity_type_id,
        activity_group_id=task_data.activity_group_id,
        assigned_to_id=task_data.assigned_to_id,
        stage_id=task_data.stage_id,
        core_group_id=task_data.core_group_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _handle_attachments(db: Session, task: TaskActivity, task_data):
    if task_data.attachments:
        for attachment_data in task_data.attachments:
            attachment = Attachment(
                task_id=task.task_id,
                file_name=attachment_data.file_name
            )
            db.add(attachment)
        db.commit()


def task_created_response(task: TaskActivity):
    return TaskCreatedResponse(
        task_id=task.task_id,
        task_name=task.task_name,
        task_description=task.task_description,
        created_by_id=task.created_by_id,
        assigned_to_id=task.assigned_to_id,
        created_on=task.created_on.isoformat(),
        modified_on=task.modified_on.isoformat(),
        status=task.status,
        favorite=task.favorite,
    )


def check_user_auth(current_user: User):
    if not current_user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")


# Helper method to determine sorting order
def get_sort_order(sort_order: str):
    return asc(TaskActivity.created_on) if sort_order == "asc" else desc(TaskActivity.created_on)


# Helper method to fetch tasks (created or assigned)
def query_tasks(db: Session, user_id: int, task_type: str, skip: int, limit: int, sort_order: str):
    order_by_clause = get_sort_order(sort_order)

    if task_type == 'created':
        # Fetch tasks created by the user
        return db.query(TaskActivity).filter(TaskActivity.created_by_id == user_id) \
            .order_by(order_by_clause).offset(skip).limit(limit).all()

    elif task_type == 'assigned':
        # Fetch tasks assigned to the user
        return db.query(TaskActivity).filter(TaskActivity.assigned_to_id == user_id) \
            .order_by(order_by_clause).offset(skip).limit(limit).all()

    return []


# Helper method to wrap tasks in the response
def wrap_task_response(tasks: List[TaskActivity]):
    task_responses = [TaskResponse.from_orm(task) for task in tasks]
    return ResponseWrapper(
        status_code=status.HTTP_200_OK,
        values=task_responses
    )


def _apply_task_updates(task: TaskActivity, task_data: dict):
    for key, value in task_data.items():
        setattr(task, key, value)
    task.modified_on = datetime.utcnow()


def _get_previous_task_data(task: TaskActivity) -> dict:
    return {
        "task_name": task.task_name,
        "task_description": task.task_description,
        "activity_type_id": task.activity_type_id,
        "activity_group_id": task.activity_group_id,
        "stage_id": task.stage_id,
        "core_group_id": task.core_group_id,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "action_type": task.action_type,
        "status": task.status,
        "link_response_ids": task.link_response_ids,
        "link_object_ids": task.link_object_ids,
        "notes": task.notes,
        "attachment_id": task.attachment_id,
        "favorite": task.favorite,
        "created_by_id": task.created_by_id,
        "assigned_to_id": task.assigned_to_id,
        "created_on": task.created_on.isoformat(),
        "modified_on": task.modified_on.isoformat()
    }


def _check_task_permissions(task: TaskActivity, current_user: User):
    if task.created_by_id != current_user.id and task.assigned_to_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Unauthorized update attempt on task {task.task_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail="You do not have permission to update this task")


def _get_task_by_id(db: Session, task_id: int) -> TaskActivity:
    task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
    if not task:
        logger.warning(f"Task with ID {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return task


async def log_task_history(db: Session, task_id: int, action: str, previous_data=None, new_data=None):
    try:
        # Convert data to JSON serializable format
        if previous_data:
            previous_data = {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in
                             previous_data.items()}
        if new_data:
            new_data = {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in
                        new_data.items()}

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


class TaskActivityImpl:
    def __init__(self):
        pass

    # Main method to create task
    async def create_task(self, db: Session, task_data, current_user):
        try:
            # Check user authentication
            check_user_auth(current_user)
            user_id = current_user.id
            logger.info(f"Creating task for user {task_data.assigned_to_id}")

            if validate_due_date(task_data.due_date):
                # Validate fields asynchronously using a ThreadPoolExecutor
                run_validations(db, task_data)

                # Create the TaskActivity after validation
                task = _create_task_entry(db, task_data, user_id)

                # Handle attachments
                _handle_attachments(db, task, task_data)

                # Log task creation history
                await log_task_history(db, task_id=task.task_id, action="Added", new_data=task_data.dict())

                logger.info(f"Task created successfully for user {user_id}, Task ID: {task.task_id}")

                response = task_created_response(task)
                # return response
                return ResponseWrapper(
                    status_code=status.HTTP_201_CREATED,
                    values=response
                )

        except HTTPException as http_exc:
            logger.error(f"HTTP error during task creation: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error creating task: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while creating the task")

        except Exception as e:
            logger.error(f"Unexpected error during task creation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # get created task based on pagination
    async def get_created_tasks(self, db: Session, current_user: User, skip: int = 0, limit: int = 10,
                                sort_order: str = 'asc'):
        try:
            check_user_auth(current_user)

            # Fetch created tasks
            tasks = query_tasks(db, user_id=current_user.id, task_type='created', skip=skip, limit=limit,
                                sort_order=sort_order)

            if not tasks:
                logger.info(f"No tasks found for user {current_user.id}")
                return ResponseWrapper(status_code=status.HTTP_200_OK, values=[])

            logger.info(f"Retrieved {len(tasks)} tasks for user {current_user.id}")

            # Wrap the tasks in the response model
            return wrap_task_response(tasks)

        except HTTPException as http_exc:
            logger.error(f"HTTP error during task retrieval: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving tasks")

        except Exception as e:
            logger.error(f"Unexpected error retrieving tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # get assigned task based on pagination
    async def get_assigned_tasks(self, db: Session, current_user: User, skip: int = 0, limit: int = 10,
                                 sort_order: str = 'asc'):
        try:
            check_user_auth(current_user)

            # Fetch assigned tasks
            tasks = query_tasks(db, user_id=current_user.id, task_type='assigned', skip=skip, limit=limit,
                                sort_order=sort_order)

            if not tasks:
                logger.info(f"No assigned tasks found for user {current_user.id}")
                return ResponseWrapper(status_code=status.HTTP_200_OK, values=[])

            logger.info(f"Retrieved {len(tasks)} assigned tasks for user {current_user.id}")

            # Wrap the tasks in the response model
            return wrap_task_response(tasks)

        except HTTPException as http_exc:
            logger.error(f"HTTP error retrieving assigned tasks: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving assigned tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving assigned tasks")

        except Exception as e:
            logger.error(f"Unexpected error retrieving assigned tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # update a task
    async def update_task(self, db: Session, task_id: int, task_data: dict, current_user: User):
        try:
            # Ensure user authentication
            check_user_auth(current_user)

            # Fetch task by ID
            task = _get_task_by_id(db, task_id)

            # Ensure the current user has permission to update the task
            _check_task_permissions(task, current_user)

            # Store the previous task data
            previous_data = _get_previous_task_data(task)

            # Apply updates to the task
            _apply_task_updates(task, task_data)

            # Commit changes to the database
            db.commit()

            # Log the changes in history
            await log_task_history(db, task_id=task.task_id, action="Modified", previous_data=previous_data,
                                   new_data=task_data)

            logger.info(f"Task with ID {task_id} updated successfully")
            return task

        except HTTPException as http_exc:
            logger.error(f"HTTP error during task update: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error updating task with ID {task_id}: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while updating the task")

        except Exception as e:
            logger.error(f"Unexpected error updating task with ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    async def get_task_by_id(self, db: Session, task_id: int, current_user: User):
        try:
            # Ensure the user is authenticated
            check_user_auth(current_user)

            # Retrieve the task by ID
            task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()

            # If task not found, raise 404 error
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

            # Check if the current user is either the creator, the assignee, or an admin
            if not current_user.is_admin and task.created_by_id != current_user.id and task.assigned_to_id != current_user.id:
                logger.warning(f"Unauthorized access attempt for task {task_id} by user {current_user.id}")
                raise HTTPException(status_code=403, detail="You do not have access to this task")

            logger.info(f"Task with ID {task_id} retrieved successfully for user {current_user.id}")

            return ResponseWrapper(
                status_code=status.HTTP_200_OK,
                values=task
            )

        except HTTPException as http_exc:
            logger.error(f"HTTP error retrieving task by ID {task_id}: {str(http_exc.detail)}")
            raise http_exc

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving task by ID {task_id} for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while retrieving the task")

        except Exception as e:
            logger.error(f"Unexpected error retrieving task by ID {task_id} for user {current_user.id}: {str(e)}")
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
            await log_task_history(db, task_id=task.task_id, action="Deleted", previous_data=previous_data)

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

