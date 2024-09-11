from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class TaskBase(BaseModel):
    task_name: str
    status: Optional[str] = "Not Started"
    favorite: Optional[bool] = False


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    task_id: int
    created_by_id: int
    assigned_to_id: Optional[int]
    created_on: datetime
    modified_on: datetime

    class Config:
        from_attributes = True  # New way in Pydantic V2


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    company: str
    is_admin: Optional[bool] = False
    picture_id: Optional[int] = None

    class Config:
        from_attributes = True  # New way in Pydantic V2


class UserResponse(BaseModel):
    username: str
    email: str

    class Config:
        from_attributes = True  # New way in Pydantic V2


class UserCreatedResponse(BaseModel):
    message: str
    user: UserResponse


class UsersResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True  # New way in Pydantic V2


class AccessToken(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True  # New way in Pydantic V2


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    action: str
    previous_data: Optional[str]
    new_data: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # New way in Pydantic V2
