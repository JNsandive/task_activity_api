import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import HTTPException, status

from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .constant import activity_type_id, activity_group_id, stage_id, core_group_id, assigned_to_id, created, assigned, \
    due_data, Modified, Added
from .models import TaskActivity, TaskHistory, User, Attachment, ActivityType, ActivityGroup, Stage, CoreGroup
from datetime import datetime, timezone
import json

from .schemas import TaskResponse, ResponseWrapper, TaskCreatedResponse, AttachmentCreate, TaskActivityCreate
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class TaskActivityImpl:
    def __init__(self):
        pass

    @staticmethod
    def validate_core_group(db: Session, core_group_id: int):
        core_group = db.query(CoreGroup).filter(CoreGroup.id == core_group_id).first()
        if not core_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Core group with id {core_group_id} does not exist."
            )
        return core_group

    @staticmethod
    def validate_activity_type(db: Session, activity_type_id: int):
        activity_type = db.query(ActivityType).filter(ActivityType.id == activity_type_id).first()
        if not activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Activity type with id {activity_type_id} does not exist."
            )
        return activity_type

    @staticmethod
    def validate_assign_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {user_id} does not exist to assign."
            )
        return user

    @staticmethod
    def validate_stage(db: Session, stage_id: int):
        stage = db.query(Stage).filter(Stage.id == stage_id).first()
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stage with id {stage_id} does not exist."
            )
        return stage

    @staticmethod
    def validate_activity_group(db: Session, activity_group_id: int):
        activity_group = db.query(ActivityGroup).filter(ActivityGroup.id == activity_group_id).first()
        if not activity_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Activity group with id {activity_group_id} does not exist."
            )
        return activity_group

    """Validate due date"""
    @staticmethod
    def validate_due_date(due_date: datetime):
        if due_date:
            # Ensure due_date is timezone-aware; if it's naive, assume it's in UTC
            if due_date.tzinfo is None or due_date.tzinfo.utcoffset(due_date) is None:
                due_date = due_date.replace(tzinfo=timezone.utc)

            # Use a timezone-aware UTC datetime for comparison
            now = datetime.now(timezone.utc)

            if due_date <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The due date must be a future date."
                )
        return True

    """Validate fields asynchronously using a ThreadPoolExecutor"""
    def run_validations(self, db: Session, task_data: dict):
        # Use ThreadPoolExecutor to validate fields concurrently
        with ThreadPoolExecutor() as executor:
            validation_tasks = []

            if task_data.get(activity_type_id) is not None:
                validation_tasks.append(executor.submit(self.validate_activity_type, db, task_data[activity_type_id]))

            if task_data.get(activity_group_id) is not None:
                validation_tasks.append(
                    executor.submit(self.validate_activity_group, db, task_data[activity_group_id]))

            if task_data.get(stage_id) is not None:
                validation_tasks.append(executor.submit(self.validate_stage, db, task_data[stage_id]))

            if task_data.get(core_group_id) is not None:
                validation_tasks.append(executor.submit(self.validate_core_group, db, task_data[core_group_id]))

            if task_data.get(assigned_to_id) is not None:
                validation_tasks.append(executor.submit(self.validate_assign_user, db, task_data[assigned_to_id]))

                # Collect the results
            for future in validation_tasks:
                future.result()  # Raise any exception

    """Create a task entry in the database"""
    @staticmethod
    def _create_task_entry_and_save(db: Session, task_data, user_id: int):
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
            core_group_id=task_data.core_group_id,
            notes=task_data.notes,
            link_response_ids=task_data.link_response_ids,
            link_object_ids=task_data.link_object_ids,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    """Updated _handle_attachments method"""

    @staticmethod
    def _handle_attachments(db: Session, task: TaskActivity, attachments: List[AttachmentCreate]):
        if attachments:
            attachment_ids = []
            for attachment_data in attachments:
                # Access the file_name using dot notation instead of brackets
                attachment = Attachment(
                    task_id=task.task_id,
                    file_name=attachment_data.file_name
                )
                db.add(attachment)
                db.commit()  # Commit to generate the attachment ID
                attachment_ids.append(attachment.id)  # Collect attachment ID
            return attachment_ids
        return []

    @staticmethod
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

    @staticmethod
    def check_user_auth(current_user: User):
        if not current_user:
            logger.warning("Unauthorized access attempt")
            raise HTTPException(status_code=401, detail="Unauthorized")

    """ Helper method to determine sorting order"""

    @staticmethod
    def get_sort_order(sort_order: str):
        return asc(TaskActivity.created_on) if sort_order == "asc" else desc(TaskActivity.created_on)

    """Helper method to fetch tasks (created or assigned)"""

    def query_tasks(self,
                    db: Session,
                    user_id: int,
                    task_type: str,
                    skip: int,
                    limit: int,
                    sort_order: str,
                    status: Optional[str] = None,
                    due_date_from: Optional[datetime] = None,
                    due_date_to: Optional[datetime] = None,
                    task_name: Optional[str] = None,
                    activity_type_id: Optional[int] = None,
                    assigned_to_id: Optional[int] = None
                    ):
        query = db.query(TaskActivity)

        # Filter by task type (created or assigned)
        if task_type == created:
            query = query.filter(TaskActivity.created_by_id == user_id)  # Get tasks created by the current user
        elif task_type == assigned:
            query = query.filter(TaskActivity.assigned_to_id == user_id)  # Get tasks assigned to the user

        # Apply additional filters dynamically based on the presence of query parameters
        if status:
            query = query.filter(TaskActivity.status == status)  # Filter by task status
        if due_date_from:
            query = query.filter(TaskActivity.due_date >= due_date_from)  # Filter by tasks due after 'due_date_from'
        if due_date_to:
            query = query.filter(TaskActivity.due_date <= due_date_to)  # Filter by tasks due before 'due_date_to'
        if task_name:
            query = query.filter(
                TaskActivity.task_name.ilike(f"%{task_name}%"))  # Filter by task name (case-insensitive)
        if activity_type_id:
            query = query.filter(TaskActivity.activity_type_id == activity_type_id)
        if assigned_to_id:
            query = query.filter(TaskActivity.assigned_to_id == assigned_to_id)

        # Sorting (ascending or descending order)
        order_by_clause = self.get_sort_order(sort_order)
        query = query.order_by(order_by_clause)

        # Pagination (skip and limit)
        query = query.offset(skip).limit(limit)

        return query.all()

    """ Helper method to wrap tasks in the response"""

    @staticmethod
    def wrap_task_response(tasks: List[TaskActivity]):
        task_responses = []

        for task in tasks:
            # Manually constructing the response instead of using from_orm to handle attachment_ids
            task_response = TaskResponse(
                task_id=task.task_id,
                task_name=task.task_name,
                task_description=task.task_description,
                status=task.status,
                favorite=task.favorite,
                due_date=task.due_date,
                action_type=task.action_type,
                activity_type_id=task.activity_type_id,
                activity_group_id=task.activity_group_id,
                stage_id=task.stage_id,
                core_group_id=task.core_group_id,
                link_response_ids=task.link_response_ids,
                link_object_ids=task.link_object_ids,
                notes=task.notes,
                attachment_ids=task.attachment_ids,
                created_on=task.created_on,
                modified_on=task.modified_on,
                created_by_id=task.created_by_id,
                assigned_to_id=task.assigned_to_id
            )
            task_responses.append(task_response)

        return ResponseWrapper(
            status_code=status.HTTP_200_OK,
            values=task_responses
        )

    # Helper method to apply task updates with handling of optional fields
    @staticmethod
    def _apply_task_updates(task: TaskActivity, task_data: dict):
        for key, value in task_data.items():
            if value is not None:
                setattr(task, key, value)

        # Ensure the modified_on field is updated
        task.modified_on = datetime.utcnow()

    @staticmethod
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
            "attachment_ids": task.attachment_ids,
            "favorite": task.favorite,
            "created_by_id": task.created_by_id,
            "assigned_to_id": task.assigned_to_id,
            "created_on": task.created_on.isoformat(),
            "modified_on": task.modified_on.isoformat()
        }

    @staticmethod
    def _check_task_permissions(task: TaskActivity, current_user: User):
        if task.created_by_id != current_user.id and task.assigned_to_id != current_user.id and not current_user.is_admin:
            logger.warning(f"Unauthorized update attempt on task {task.task_id} by user {current_user.id}")
            raise HTTPException(status_code=403, detail="You do not have permission to update this task")

    @staticmethod
    def _get_task_by_id(db: Session, task_id: int) -> TaskActivity:
        task = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        return task

    """Log task history"""

    async def log_task_history(self, db: Session, task_id: int, action: str, current_user: User, previous_data=None,
                               new_data=None):
        try:
            # Convert previous_data and new_data from model objects to dictionaries if necessary
            if previous_data and not isinstance(previous_data, dict):
                previous_data = {column.name: getattr(previous_data, column.name) for column in
                                 previous_data.__table__.columns}

            if new_data and not isinstance(new_data, dict):
                new_data = {column.name: getattr(new_data, column.name) for column in new_data.__table__.columns}

            # Ensure data is JSON serializable
            if previous_data:
                previous_data = {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in
                                 previous_data.items()}
            if new_data:
                new_data = {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in
                            new_data.items()}

            # Log the history entry
            history_entry = TaskHistory(
                task_id=task_id, action=action, previous_data=json.dumps(previous_data) if previous_data else None,
                new_data=json.dumps(new_data) if new_data else None, created_at=datetime.utcnow(),
                modified_by_id=current_user.id  # Store the user who modified the task
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

    @staticmethod
    def _delete_task_history(db: Session, task_id: int):
        try:
            # Delete all history records associated with the task ID
            db.query(TaskHistory).filter(TaskHistory.task_id == task_id).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Deleted all history records for task ID {task_id}")

        except SQLAlchemyError as e:
            logger.error(f"Error deleting task history for task ID {task_id}: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An error occurred while deleting task history")

    @staticmethod
    def _check_user_permission(current_user, task, task_id):
        # Check if the current user is either the creator, the assignee, or an admin
        if not current_user.is_admin and task.created_by_id != current_user.id and task.assigned_to_id != current_user.id:
            logger.warning(f"Unauthorized access attempt for task {task_id} by user {current_user.id}")
            raise HTTPException(status_code=403, detail="You do not have access to this task")

    @staticmethod
    def send_task_assigned_email(to_email: str, task_name: str, due_date: datetime, description: str, assignor: str):
        # Email body
        email_content = f"""
        Hello,

        You have been assigned a new task by: {assignor}
        Task Name: {task_name}
        Description: {description}
        Due Date: {due_date.strftime('%Y-%m-%d %H:%M:%S')}

        Please complete it before the due date.

        Best Regards,
        Task Management System
        """

        # Set up email content and headers
        msg = MIMEText(email_content)
        msg['Subject'] = f"New Task Assigned: {task_name}"
        msg['From'] = os.getenv('SMTP_USERNAME')
        msg['To'] = to_email
        # Gmail SMTP server credentials
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        try:
            # Set up connection with Gmail's SMTP server
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()  # Identify yourself to the server
                server.starttls()  # Secure the connection
                server.ehlo()  # Re-identify yourself after starting TLS
                server.login(smtp_username, smtp_password)  # Login
                server.sendmail(smtp_username, to_email, msg.as_string())  # Send the email
                logger.info("Email sent successfully")
        except smtplib.SMTPException as e:
            logger.error(f"Error sending email: {e}")
            raise e

    """Main method to create task"""

    async def create_task(self, db: Session, task_data: TaskActivityCreate, current_user: User):
        try:
            if self.validate_due_date(task_data.due_date):
                # Validate fields asynchronously using a ThreadPoolExecutor
                self.run_validations(db, task_data.dict())

                task = self._create_task_entry_and_save(db, task_data, current_user.id)

                # Handle and attach attachments
                attachment_ids = []
                if task_data.attachments:
                    attachment_ids = self._handle_attachments(db, task=task, attachments=task_data.attachments)

                # Update the task with the list of attachment IDs
                if attachment_ids:
                    task.attachment_ids = attachment_ids

                # Log task creation history
                await self.log_task_history(db, task_id=task.task_id, action=Added, new_data=task_data.dict(),
                                            current_user=current_user)

                logger.info(f"Task created successfully for user {current_user.username}, Task ID: {task.task_id}")

                # Assuming User model has an "email" field
                get_assigned_user_email = db.query(User.email).filter(User.id == task.assigned_to_id).scalar()

                if get_assigned_user_email:
                    # Send email notification to the assigned user
                    self.send_task_assigned_email(
                        to_email=get_assigned_user_email, task_name=task.task_name, due_date=task.due_date,
                        description=task.task_description, assignor=current_user.username
                    )

                response = self.task_created_response(task)

                return ResponseWrapper(
                    status_code=status.HTTP_201_CREATED,
                    values=response
                )
        except Exception as e:
            logger.error(f"Unexpected error during task creation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    """get created task based on pagination"""

    async def get_tasks(
            self,
            db: Session, current_user: User, task_type: str, skip: int = 0, limit: int = 10, sort_order: str = 'asc',
            _status: Optional[str] = None, due_date_from: Optional[datetime] = None,
            due_date_to: Optional[datetime] = None, task_name: Optional[str] = None,
            activity_type_id: Optional[int] = None,
            assigned_to_id: Optional[int] = None
    ):
        try:
            if activity_type_id:
                self.validate_activity_type(db, activity_type_id)
            if assigned_to_id:
                self.validate_assign_user(db, assigned_to_id)

            # Fetch tasks with filters, based on the task_type (created or assigned)
            tasks = self.query_tasks(
                db, user_id=current_user.id, task_type=task_type, skip=skip, limit=limit, sort_order=sort_order,
                status=_status, due_date_from=due_date_from, due_date_to=due_date_to, task_name=task_name,
                assigned_to_id=assigned_to_id, activity_type_id=activity_type_id
            )

            if not tasks:
                logger.info(f"No tasks found for user {current_user.id}")
                return ResponseWrapper(status_code=status.HTTP_200_OK, values=[])

            logger.info(f"Retrieved {len(tasks)} {task_type} tasks for user {current_user.id}")

            # Wrap the tasks in the response model
            return self.wrap_task_response(tasks)

        except Exception as e:
            logger.error(f"Unexpected error retrieving tasks for user {current_user.id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    """update a task"""

    async def update_task(self, db: Session, task_id: int, task_data: dict, current_user: User):
        try:

            if due_data in task_data:
                self.validate_due_date(task_data.get(due_data))

            # Fetch task by ID
            task = self._get_task_by_id(db, task_id)

            self.run_validations(db, task_data)

            # Ensure the current user has permission to update the task
            self._check_task_permissions(task, current_user)

            # Store the previous task data
            previous_data = self._get_previous_task_data(task)

            # Handle attachments if provided
            if 'attachments' in task_data and task_data['attachments'] is not None:
                # Convert dictionaries to AttachmentCreate models
                attachments = [AttachmentCreate(**attachment) for attachment in task_data['attachments']]
                attachment_ids = self._handle_attachments(db, task, attachments)
                task.attachment_ids = attachment_ids  # Update the task's attachment IDs
                db.commit()  # Commit the change to update the task with attachment IDs

            # Apply updates to the task (merge the dictionary into the task instance)
            for key, value in task_data.items():
                if key == 'attachments':  # Skip the attachments field
                    continue
                if value is not None:  # Only update fields if value is provided
                    setattr(task, key, value)

            get_assigned_user_email = db.query(User.email).filter(User.id == task.assigned_to_id).scalar()

            self.send_task_assigned_email(
                to_email=get_assigned_user_email, task_name=task.task_name, due_date=task.due_date,
                description=task.task_description, assignor=current_user.username
            )
            # Update modified timestamp
            task.modified_on = datetime.utcnow()

            # Commit changes to the database
            db.commit()
            db.refresh(task)

            task = self._get_task_by_id(db, task_id)

            # Log the changes in history
            await self.log_task_history(db, task_id=task.task_id, action=Modified, previous_data=previous_data,
                                        new_data=task, current_user=current_user)

            logger.info(f"Task with ID {str(task.task_id)} updated successfully")
            return ResponseWrapper(
                status_code=status.HTTP_200_OK,
                values=task
            )

        except Exception as e:
            logger.error(f"Unexpected error updating task with ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred")

    async def get_task_by_id(self, db: Session, task_id: int, current_user: User):
        try:
            # Retrieve the task by ID
            task = self._get_task_by_id(db, task_id)

            # Check if the task exists
            if not task:
                logger.warning(f"No task found with ID {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No task found !"
                )

            # Convert the task to the response format
            task_response = TaskResponse.from_orm(task)

            # Return the wrapped response
            return ResponseWrapper(
                status_code=status.HTTP_200_OK,
                values=task_response
            )

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error retrieving task by ID {task_id} for user {current_user.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while retrieving the task."
            )

    # delete a task
    async def delete_task(self, db: Session, task_id: int, current_user: User):
        try:

            # Fetch the task by ID
            task = self._get_task_by_id(db, task_id)
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(status_code=404, detail=f"Task not found")

            self._check_user_permission(current_user, task, task_id)

            # Delete task history records before deleting the task itself
            self._delete_task_history(db, task_id)

            # Now delete the task itself
            db.delete(task)
            db.commit()

            logger.info(f"Task with ID {task_id} deleted successfully")
            return ResponseWrapper(
                status_code=status.HTTP_204_NO_CONTENT,
                values={}
            )

        except Exception as e:
            logger.error(f"Unexpected error deleting task with ID {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred")
