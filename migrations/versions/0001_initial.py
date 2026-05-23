"""initial schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topics_level"), "topics", ["level"], unique=False)
    op.create_index(op.f("ix_topics_slug"), "topics", ["slug"], unique=True)

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("level_mode", sa.String(length=16), nullable=False),
        sa.Column("daily_new_words", sa.Integer(), nullable=False),
        sa.Column("typing_direction", sa.String(length=16), nullable=False),
        sa.Column("show_transcription", sa.Boolean(), nullable=False),
        sa.Column("show_examples", sa.Boolean(), nullable=False),
        sa.Column("hard_words_more_often", sa.Boolean(), nullable=False),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_time", sa.Time(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "words",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("greek", sa.String(length=255), nullable=False),
        sa.Column("transcription", sa.String(length=255), nullable=True),
        sa.Column("ru", sa.String(length=255), nullable=False),
        sa.Column("part_of_speech", sa.String(length=64), nullable=True),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_words_greek"), "words", ["greek"], unique=False)
    op.create_index(op.f("ix_words_is_active"), "words", ["is_active"], unique=False)
    op.create_index(op.f("ix_words_level"), "words", ["level"], unique=False)
    op.create_index(op.f("ix_words_ru"), "words", ["ru"], unique=False)
    op.create_index(op.f("ix_words_slug"), "words", ["slug"], unique=True)

    op.create_table(
        "answer_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_answer_attempts_created_at"), "answer_attempts", ["created_at"], unique=False)
    op.create_index(op.f("ix_answer_attempts_direction"), "answer_attempts", ["direction"], unique=False)
    op.create_index(op.f("ix_answer_attempts_is_correct"), "answer_attempts", ["is_correct"], unique=False)
    op.create_index(op.f("ix_answer_attempts_task_type"), "answer_attempts", ["task_type"], unique=False)
    op.create_index(op.f("ix_answer_attempts_user_id"), "answer_attempts", ["user_id"], unique=False)
    op.create_index(op.f("ix_answer_attempts_word_id"), "answer_attempts", ["word_id"], unique=False)

    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("new_words_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date"),
    )
    op.create_index(op.f("ix_daily_stats_date"), "daily_stats", ["date"], unique=False)
    op.create_index(op.f("ix_daily_stats_user_id"), "daily_stats", ["user_id"], unique=False)

    op.create_table(
        "user_current_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("bot_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_current_tasks_task_type"), "user_current_tasks", ["task_type"], unique=False)
    op.create_index(op.f("ix_user_current_tasks_user_id"), "user_current_tasks", ["user_id"], unique=True)

    op.create_table(
        "user_word_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("box", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False),
        sa.Column("last_answer_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("is_hard", sa.Boolean(), nullable=False),
        sa.Column("is_learned", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "word_id"),
    )
    op.create_index(op.f("ix_user_word_progress_box"), "user_word_progress", ["box"], unique=False)
    op.create_index(op.f("ix_user_word_progress_is_hard"), "user_word_progress", ["is_hard"], unique=False)
    op.create_index(op.f("ix_user_word_progress_is_learned"), "user_word_progress", ["is_learned"], unique=False)
    op.create_index(op.f("ix_user_word_progress_next_review_at"), "user_word_progress", ["next_review_at"], unique=False)
    op.create_index(op.f("ix_user_word_progress_user_id"), "user_word_progress", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_word_progress_word_id"), "user_word_progress", ["word_id"], unique=False)

    op.create_table(
        "word_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("answer", sa.String(length=255), nullable=False),
        sa.Column("normalized_answer", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word_id", "direction", "normalized_answer"),
    )
    op.create_index(op.f("ix_word_answers_direction"), "word_answers", ["direction"], unique=False)
    op.create_index(op.f("ix_word_answers_normalized_answer"), "word_answers", ["normalized_answer"], unique=False)
    op.create_index(op.f("ix_word_answers_word_id"), "word_answers", ["word_id"], unique=False)

    op.create_table(
        "word_examples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column("example_el", sa.Text(), nullable=False),
        sa.Column("example_ru", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_word_examples_word_id"), "word_examples", ["word_id"], unique=False)


def downgrade() -> None:
    op.drop_table("word_examples")
    op.drop_table("word_answers")
    op.drop_table("user_word_progress")
    op.drop_table("user_current_tasks")
    op.drop_table("daily_stats")
    op.drop_table("answer_attempts")
    op.drop_table("words")
    op.drop_table("user_settings")
    op.drop_table("topics")
    op.drop_table("users")
