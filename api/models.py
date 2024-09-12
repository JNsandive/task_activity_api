from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TaskActivity(Base):
    __tablename__ = "tasks_activity"

    task_id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), index=True, nullable=False)
    task_description = Column(String, nullable=True)

    # Activity, stage, and core group fields (normalized with IDs from other tables)
    activity_type_id = Column(Integer, ForeignKey('activity_types.id'), nullable=False)
    activity_group_id = Column(Integer, ForeignKey('activity_groups.id'), nullable=True)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=True)
    core_group_id = Column(Integer, ForeignKey('core_groups.id'), nullable=True)

    # Task-related fields
    due_date = Column(DateTime, nullable=True)
    action_type = Column(String(100), nullable=True)
    status = Column(String(50), default="Not Started", nullable=False)

    # Fields for LinkResponseID and LinkObjectID
    link_response_ids = Column(ARRAY(Integer), nullable=True)  # PostgreSQL Array of integers
    link_object_ids = Column(ARRAY(Integer), nullable=True)  # PostgreSQL Array of integers

    # Notes and attachments
    notes = Column(String, nullable=True)  # No max length specified for notes
    attachment_ids = Column(ARRAY(Integer), nullable=True)  # Updated: Array of attachment IDs

    # Created and modified metadata fields
    created_on = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_on = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Boolean field for favorite
    favorite = Column(String(100), nullable=True)

    # Foreign keys to link users (creator and assignee)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship with TaskHistory
    history = relationship("TaskHistory", back_populates="task")
    attachments = relationship("Attachment", back_populates="task")  # One-to-many relationship with Attachments
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="tasks_created")
    assignee = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tasks")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    company = Column(String(255), nullable=True)
    picture_id = Column(Integer, nullable=True)

    # Relationship with tasks created by the user
    tasks_created = relationship("TaskActivity", foreign_keys=[TaskActivity.created_by_id], back_populates="creator")

    # Relationship with tasks assigned to the user
    assigned_tasks = relationship("TaskActivity", foreign_keys=[TaskActivity.assigned_to_id], back_populates="assignee")


# Table for ActivityType
class ActivityType(Base):
    __tablename__ = "activity_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Max length 100 characters


# Table for ActivityGroup
class ActivityGroup(Base):
    __tablename__ = "activity_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Max length 100 characters
    sub_category_id = Column(Integer, nullable=True)
    sub_category_name = Column(String(100), nullable=True)  # Max length 100 characters


# Table for Stage
class Stage(Base):
    __tablename__ = "stages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Max length 100 characters


# Table for CoreGroup
class CoreGroup(Base):
    __tablename__ = "core_groups"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True)  # Max length 100 characters
    name = Column(String(255), nullable=True)  # Max length 255 characters


# Table for RelatedEntity
class RelatedEntity(Base):
    __tablename__ = "related_entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    picture_id = Column(Integer, nullable=True)
    company = Column(String(255), nullable=True)


# Table for Attachment
class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks_activity.task_id'))
    file_name = Column(String(255), nullable=True)

    task = relationship("TaskActivity", back_populates="attachments")


# Table for TaskHistory
class TaskHistory(Base):
    __tablename__ = "tasks_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks_activity.task_id"), nullable=False)
    action = Column(String(50), nullable=False)
    previous_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Ensure this is correctly defined
    modified_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    modified_by = relationship("User", foreign_keys=[modified_by_id])
    task = relationship("TaskActivity", back_populates="history")
