"""Add word lesson metadata.

Revision ID: 0004_word_lessons
Revises: 0003_sentence_progress
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_word_lessons"
down_revision = "0003_sentence_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("words", sa.Column("lesson", sa.String(length=64), nullable=True))
    op.add_column("words", sa.Column("lessons", sa.Text(), nullable=True))
    op.create_index("ix_words_lesson", "words", ["lesson"])


def downgrade() -> None:
    op.drop_index("ix_words_lesson", table_name="words")
    op.drop_column("words", "lessons")
    op.drop_column("words", "lesson")
