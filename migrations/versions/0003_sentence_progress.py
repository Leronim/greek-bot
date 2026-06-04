"""add sentence progress

Revision ID: 0003_sentence_progress
Revises: 0002_current_task_bot_message_id
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_sentence_progress"
down_revision: Union[str, None] = "0002_current_task_bot_message_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sentence_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sentence_id", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("correct_streak", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False),
        sa.Column("last_answer_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sentence_id", "task_type", "direction"),
    )
    op.create_index(op.f("ix_sentence_progress_direction"), "sentence_progress", ["direction"], unique=False)
    op.create_index(op.f("ix_sentence_progress_sentence_id"), "sentence_progress", ["sentence_id"], unique=False)
    op.create_index(op.f("ix_sentence_progress_task_type"), "sentence_progress", ["task_type"], unique=False)
    op.create_index(op.f("ix_sentence_progress_user_id"), "sentence_progress", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sentence_progress_user_id"), table_name="sentence_progress")
    op.drop_index(op.f("ix_sentence_progress_task_type"), table_name="sentence_progress")
    op.drop_index(op.f("ix_sentence_progress_sentence_id"), table_name="sentence_progress")
    op.drop_index(op.f("ix_sentence_progress_direction"), table_name="sentence_progress")
    op.drop_table("sentence_progress")
