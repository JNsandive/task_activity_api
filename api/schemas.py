from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, TypeVar, Generic

from pydantic.generics import GenericModel

# Create a type variable that can represent any schema type
T = TypeVar('T')


# Generic response wrapper
class ResponseWrapper(GenericModel, Generic[T]):
    status_code: int
    values: T

    class Config:
        arbitrary_types_allowed = True


class TaskBase(BaseModel):
    task_name: str
    task_description: Optional[str] = None
    status: Optional[str] = "In Active"
    favorite: Optional[bool] = False

    class Config:
        orm_mode = True


# Attachment schema
class AttachmentCreate(BaseModel):
    file_name: str


class TaskActivityCreate(TaskBase):
    activity_type_id: Optional[int] = None
    activity_group_id: Optional[int] = None
    stage_id: Optional[int] = None
    core_group_id: Optional[int] = None
    due_date: Optional[datetime] = None
    action_type: Optional[str] = None
    link_response_ids: Optional[List[int]] = None
    link_object_ids: Optional[List[int]] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None
    attachments: Optional[List[AttachmentCreate]] = None

    class Config:
        orm_mode = True


class TaskCreatedResponse(TaskBase):
    task_id: int
    created_by_id: int
    assigned_to_id: Optional[int]
    created_on: str
    modified_on: str

    class Config:
        orm_mode = True


class TaskResponse(TaskBase):
    task_id: int
    activity_type_id: int
    activity_group_id: Optional[int]
    stage_id: Optional[int]
    core_group_id: Optional[int]
    due_date: Optional[datetime]
    action_type: Optional[str]
    link_response_ids: Optional[List[int]]
    link_object_ids: Optional[List[int]]
    notes: Optional[str]
    attachment_ids: Optional[List[int]]
    created_on: datetime
    modified_on: datetime
    created_by_id: int
    assigned_to_id: Optional[int]

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    company: str
    is_admin: Optional[bool] = False
    picture_id: Optional[int] = None

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    username: str
    email: str

    class Config:
        orm_mode = True


class UserCreatedResponse(BaseModel):
    message: str
    user: UserResponse


class UsersResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class AccessToken(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True


class TaskHistoryResponse(BaseModel):
    Activity_Object: dict
    Activity_name: str
    Activity: str
    Created_by: str
    Created_at: datetime


class TaskDataResponse(BaseModel):
    status: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None


class TaskHistoryDetailsResponse(BaseModel):
    previous_data_value: TaskDataResponse
    latest_data_value: TaskDataResponse
