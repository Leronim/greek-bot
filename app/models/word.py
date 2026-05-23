from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(8), index=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    words = relationship("Word", back_populates="topic")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    level: Mapped[str] = mapped_column(String(8), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    greek: Mapped[str] = mapped_column(String(255), index=True)
    transcription: Mapped[str] = mapped_column(String(255), nullable=True)
    ru: Mapped[str] = mapped_column(String(255), index=True)
    part_of_speech: Mapped[str] = mapped_column(String(64), nullable=True)
    gender: Mapped[str] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic = relationship("Topic", back_populates="words")
    answers = relationship("WordAnswer", back_populates="word", cascade="all, delete-orphan")
    examples = relationship("WordExample", back_populates="word", cascade="all, delete-orphan")


class WordAnswer(Base):
    __tablename__ = "word_answers"
    __table_args__ = (UniqueConstraint("word_id", "direction", "normalized_answer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    direction: Mapped[str] = mapped_column(String(16), index=True)
    answer: Mapped[str] = mapped_column(String(255))
    normalized_answer: Mapped[str] = mapped_column(String(255), index=True)

    word = relationship("Word", back_populates="answers")


class WordExample(Base):
    __tablename__ = "word_examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    example_el: Mapped[str] = mapped_column(Text)
    example_ru: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0)

    word = relationship("Word", back_populates="examples")
