from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import User, UserSettings
from app.repositories.progress_repo import count_due_reviews


def create_scheduler(bot: Bot, session_factory: async_sessionmaker) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminders, "interval", minutes=1, args=[bot, session_factory])
    return scheduler


async def send_daily_reminders(bot: Bot, session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(User, UserSettings)
            .join(UserSettings, UserSettings.user_id == User.id)
            .where(UserSettings.reminders_enabled.is_(True))
        )
        for user, settings in result.all():
            due_count = await count_due_reviews(session, user.id)
            await bot.send_message(
                user.telegram_id,
                "Γεια σου!\n\n"
                f"Сегодня:\n{due_count} слов на повторение\n\n"
                "Открой /menu, чтобы начать.",
            )
