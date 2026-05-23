from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyStats, User, UserWordProgress, Word
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


async def admin_daily_activity(session: AsyncSession, limit: int = 14) -> list[dict[str, int | str]]:
    result = await session.execute(
        select(
            DailyStats.date,
            func.count(DailyStats.user_id).label("active_users"),
            func.coalesce(func.sum(DailyStats.new_words_count), 0).label("new_words"),
            func.coalesce(func.sum(DailyStats.review_count), 0).label("reviews"),
            func.coalesce(func.sum(DailyStats.correct_count), 0).label("correct"),
            func.coalesce(func.sum(DailyStats.wrong_count), 0).label("wrong"),
        )
        .group_by(DailyStats.date)
        .order_by(DailyStats.date.desc())
        .limit(limit)
    )
    rows = []
    for row in result.all():
        correct = int(row.correct or 0)
        wrong = int(row.wrong or 0)
        attempts = correct + wrong
        accuracy = round(correct / attempts * 100) if attempts else 0
        rows.append(
            {
                "date": row.date.isoformat(),
                "active_users": int(row.active_users or 0),
                "new_words": int(row.new_words or 0),
                "reviews": int(row.reviews or 0),
                "attempts": attempts,
                "accuracy": accuracy,
            }
        )
    return rows


async def build_admin_stats_text(session: AsyncSession) -> str:
    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_words = await session.scalar(select(func.count(Word.id)).where(Word.is_active.is_(True))) or 0
    rows = await admin_daily_activity(session, limit=7)
    lines = [
        "📈 Статистика бота",
        "",
        f"Пользователей всего: {total_users}",
        f"Активных слов: {total_words}",
        "",
        "Активность по дням:",
    ]
    if not rows:
        lines.append("Пока нет данных.")
    for row in rows:
        lines.append(
            f"{row['date']}: {row['active_users']} уник., "
            f"{row['attempts']} действий, точность {row['accuracy']}%"
        )
    return "\n".join(lines)
