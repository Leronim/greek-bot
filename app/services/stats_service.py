from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserWordProgress, Word
from app.repositories.attempts_repo import attempts_totals
from app.repositories.progress_repo import count_due_reviews


async def build_stats_text(session: AsyncSession, user_id: int) -> str:
    total_words = await session.scalar(select(func.count(Word.id)).where(Word.is_active.is_(True))) or 0
    studied = await session.scalar(select(func.count(UserWordProgress.id)).where(UserWordProgress.user_id == user_id)) or 0
    learned = await session.scalar(
        select(func.count(UserWordProgress.id)).where(
            UserWordProgress.user_id == user_id,
            UserWordProgress.is_learned.is_(True),
        )
    ) or 0
    due = await count_due_reviews(session, user_id)
    correct, attempts = await attempts_totals(session, user_id)
    accuracy = round(correct / attempts * 100) if attempts else 0

    a1_total = await session.scalar(select(func.count(Word.id)).where(Word.level == "A1", Word.is_active.is_(True))) or 0
    a1_done = await _count_studied_by_level(session, user_id, "A1")

    return (
        "📊 Твой прогресс\n\n"
        f"Всего слов в базе: {total_words}\n"
        f"Изучено: {studied} слов\n"
        f"Выучено: {learned} слов\n"
        f"На повторении: {due} слов\n\n"
        f"Точность: {accuracy}%\n\n"
        f"A1: {a1_done}/{a1_total}"
    )


async def _count_studied_by_level(session: AsyncSession, user_id: int, level: str) -> int:
    result = await session.execute(
        select(func.count(UserWordProgress.id))
        .join(Word, Word.id == UserWordProgress.word_id)
        .where(UserWordProgress.user_id == user_id, Word.level == level)
    )
    return result.scalar_one()
