"""Initial migration

Revision ID: bb2c4d5a9ebe
Revises: 
Create Date: 2024-09-10 14:12:28.695030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bb2c4d5a9ebe'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tasks_activity',
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('task_name', sa.String(length=255), nullable=False),
    sa.Column('task_description', sa.Text(), nullable=True),
    sa.Column('activity_type_id', sa.Integer(), nullable=False),
    sa.Column('activity_type_name', sa.String(length=100), nullable=False),
    sa.Column('activity_group_sub_category_id', sa.Integer(), nullable=True),
    sa.Column('activity_group_sub_category_name', sa.String(length=100), nullable=True),
    sa.Column('activity_group_id', sa.Integer(), nullable=True),
    sa.Column('activity_group_name', sa.String(length=100), nullable=True),
    sa.Column('stage_id', sa.Integer(), nullable=True),
    sa.Column('stage_name', sa.String(length=100), nullable=True),
    sa.Column('core_group_category_id', sa.Integer(), nullable=True),
    sa.Column('core_group_category', sa.String(length=100), nullable=True),
    sa.Column('core_group_id', sa.Integer(), nullable=True),
    sa.Column('core_group_name', sa.String(length=255), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('action_type', sa.String(length=100), nullable=True),
    sa.Column('related_to', sa.String(length=255), nullable=True),
    sa.Column('related_to_picture_id', sa.Integer(), nullable=True),
    sa.Column('related_to_email', sa.String(length=255), nullable=True),
    sa.Column('related_to_company', sa.String(length=255), nullable=True),
    sa.Column('assigned_to', sa.String(length=255), nullable=False),
    sa.Column('assigned_to_picture_id', sa.Integer(), nullable=True),
    sa.Column('assigned_to_email', sa.String(length=255), nullable=True),
    sa.Column('assigned_to_company', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('attachment_id', sa.Integer(), nullable=True),
    sa.Column('attachments', sa.String(length=255), nullable=True),
    sa.Column('link_response_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
    sa.Column('link_object_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
    sa.Column('created_by', sa.String(length=255), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('modified_by', sa.String(length=255), nullable=True),
    sa.Column('modified_on', sa.DateTime(), nullable=False),
    sa.Column('key', sa.String(length=255), nullable=True),
    sa.Column('favorite', sa.String(length=5), nullable=True),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('task_id')
    )
    op.create_index(op.f('ix_tasks_activity_task_id'), 'tasks_activity', ['task_id'], unique=False)
    op.create_index(op.f('ix_tasks_activity_task_name'), 'tasks_activity', ['task_name'], unique=False)
    op.create_table('tasks_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('previous_data', sa.Text(), nullable=True),
    sa.Column('new_data', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks_activity.task_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_history_id'), 'tasks_history', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tasks_history_id'), table_name='tasks_history')
    op.drop_table('tasks_history')
    op.drop_index(op.f('ix_tasks_activity_task_name'), table_name='tasks_activity')
    op.drop_index(op.f('ix_tasks_activity_task_id'), table_name='tasks_activity')
    op.drop_table('tasks_activity')
    # ### end Alembic commands ###
