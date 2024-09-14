import json
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.models import TaskHistory, User
from api.schemas import TaskHistoryResponse, ResponseWrapper, TaskHistoryDetailsResponse, TaskDataResponse

logger = logging.getLogger(__name__)


class TasksHistory():

    def __init__(self):
        pass

    @staticmethod
    def _get_order_by_clause(sort_order: str):
        """Return the order by clause based on the sort order."""
        if sort_order == "asc":
            return TaskHistory.created_at.asc()
        return TaskHistory.created_at.desc()

    @staticmethod
    def _format_entry(entry: TaskHistory, user_name: str):
        """Format a single task history entry."""
        new_data = json.loads(entry.new_data) if entry.new_data else {}
        task_name = new_data.get("task_name", "N/A")
        _status = new_data.get("status", "N/A")

        return {
            "Activity_Object": new_data,
            "Activity_name": task_name,
            "Activity": _status,
            "Created_by": user_name,  # Use user_name instead of ID
            "Created_at": entry.created_at
        }

    @staticmethod
    def _get_deserialized_data(data):
        """Helper method to deserialize JSON data."""
        return json.loads(data) if data else {}

    @staticmethod
    def _create_task_history_detail(field_name, previous_value, latest_value):
        """Helper method to create TaskHistoryDetailsResponse."""
        return TaskHistoryDetailsResponse(
            field_name=field_name,
            previous_data_value=previous_value,
            latest_data_value=latest_value
        )

    @staticmethod
    def _get_user_name(db: Session, user_id: int):
        """Fetch the user's name using the user_id."""
        user = db.query(User).filter(User.id == user_id).first()
        return user.name if user else "N/A"

    @staticmethod
    def _get_deserialized_data(data):
        """Helper method to deserialize JSON data."""
        return json.loads(data) if data else {}

    @staticmethod
    def _get_user_name(db: Session, user_id: int):
        """Fetch the user's name using the user_id."""
        user = db.query(User).filter(User.id == user_id).first()
        return user.username if user else "N/A"

    async def get_all_task_histories(self,
                                     db: Session,
                                     skip: int = 0,
                                     limit: int = 10,
                                     sort_order: str = 'asc'):
        """Get all task histories."""
        try:
            # Get the order by clause
            order_by_clause = self._get_order_by_clause(sort_order)

            # Join TaskHistory with User table to get the name of the user who modified the task
            history_entries = db.query(TaskHistory, User.username).join(User, TaskHistory.modified_by_id == User.id) \
                .order_by(order_by_clause).offset(skip).limit(limit).all()

            # Format the response using the fetched User.name
            formatted_response = [self._format_entry(entry[0], entry[1]) for entry in history_entries]

            return ResponseWrapper(
                status_code=status.HTTP_200_OK,
                values=formatted_response
            )

        except Exception as e:
            logger.error(f"Error fetching task histories: {str(e)}")
            raise

    async def get_task_history_details(self, task_id: int, db: Session):
        """Get details of the task history"""
        try:
            task_history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()

            if not task_history:
                raise HTTPException(status_code=404, detail="Task history not found")

            # Take the latest task history and previous one, assuming you want the first two records
            latest_task = task_history[-1]
            previous_task = task_history[-2] if len(task_history) > 1 else None  # Check if a previous task exists

            # Deserialize previous and latest data
            latest_data = self._get_deserialized_data(latest_task.new_data)
            previous_data = self._get_deserialized_data(previous_task.previous_data) if previous_task else {}

            # Fetch user names
            latest_user_name = self._get_user_name(db, latest_task.modified_by_id)
            previous_user_name = self._get_user_name(db, previous_task.modified_by_id) if previous_task else "N/A"

            # Construct the response
            task_history_response = TaskHistoryDetailsResponse(
                previous_data_value=TaskDataResponse(
                    status=previous_data.get("status", "N/A"),
                    created_by=previous_user_name,
                    created_at=previous_task.created_at.strftime("%m/%d/%y %H:%M")

                ),
                latest_data_value=TaskDataResponse(
                    status=latest_data.get("status", "N/A"),
                    created_by=latest_user_name,
                    created_at=latest_task.created_at.strftime("%m/%d/%y %H:%M")
                )
            )

            # Return the response wrapped in ResponseWrapper
            return ResponseWrapper(
                status_code=status.HTTP_200_OK,
                values=task_history_response
            )

        except Exception as e:
            logger.error(f"Error fetching task history details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
