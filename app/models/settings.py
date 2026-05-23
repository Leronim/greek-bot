from datetime import datetime, time

from sqlalchemy import DateTime, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings as app_settings
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    level_mode: Mapped[str] = mapped_column(String(16), default="A1")
    daily_new_words: Mapped[int] = mapped_column(default=5)
    typing_direction: Mapped[str] = mapped_column(String(16), default="mixed")
    show_transcription: Mapped[bool] = mapped_column(default=True)
    show_examples: Mapped[bool] = mapped_column(default=True)
    hard_words_more_often: Mapped[bool] = mapped_column(default=True)
    reminders_enabled: Mapped[bool] = mapped_column(default=False)
    reminder_time: Mapped[time] = mapped_column(Time(), default=time(hour=10, minute=0))
    timezone: Mapped[str] = mapped_column(String(64), default=app_settings.default_timezone)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings")
