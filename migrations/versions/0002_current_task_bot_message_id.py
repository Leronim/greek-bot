"""add bot message id to current task

Revision ID: 0002_current_task_bot_message_id
Revises: 0001_initial
Create Date: 2026-05-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_current_task_bot_message_id"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("user_current_tasks")}
    if "bot_message_id" not in columns:
        op.add_column("user_current_tasks", sa.Column("bot_message_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("user_current_tasks")}
    if "bot_message_id" in columns:
        op.drop_column("user_current_tasks", "bot_message_id")
