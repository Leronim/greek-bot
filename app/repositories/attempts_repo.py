from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnswerAttempt, DailyStats


async def add_attempt(
    session: AsyncSession,
    user_id: int,
    word_id: int,
    task_type: str,
    direction: str,
    user_answer: str,
    is_correct: bool,
) -> AnswerAttempt:
    attempt = AnswerAttempt(
        user_id=user_id,
        word_id=word_id,
        task_type=task_type,
        direction=direction,
        user_answer=user_answer,
        is_correct=is_correct,
    )
    session.add(attempt)
    await session.flush()
    return attempt


async def bump_daily_stats(session: AsyncSession, user_id: int, is_correct: bool, is_new: bool = False) -> None:
    stats = await get_or_create_daily_stats(session, user_id)
    if is_new:
        stats.new_words_count += 1
    else:
        stats.review_count += 1
    if is_correct:
        stats.correct_count += 1
    else:
        stats.wrong_count += 1


async def get_or_create_daily_stats(session: AsyncSession, user_id: int) -> DailyStats:
    today = date.today()
    result = await session.execute(select(DailyStats).where(DailyStats.user_id == user_id, DailyStats.date == today))
    stats = result.scalar_one_or_none()
    if stats is None:
        stats = DailyStats(user_id=user_id, date=today)
        session.add(stats)
        await session.flush()
    return stats


async def touch_daily_activity(session: AsyncSession, user_id: int) -> None:
    await get_or_create_daily_stats(session, user_id)


async def attempts_totals(session: AsyncSession, user_id: int) -> tuple[int, int]:
    correct = await session.execute(
        select(func.count(AnswerAttempt.id)).where(AnswerAttempt.user_id == user_id, AnswerAttempt.is_correct.is_(True))
    )
    total = await session.execute(select(func.count(AnswerAttempt.id)).where(AnswerAttempt.user_id == user_id))
    return correct.scalar_one(), total.scalar_one()


async def recent_attempt_word_ids(session: AsyncSession, user_id: int, task_type: str, limit: int = 25) -> list[int]:
    result = await session.execute(
        select(AnswerAttempt.word_id)
        .where(AnswerAttempt.user_id == user_id, AnswerAttempt.task_type == task_type)
        .order_by(AnswerAttempt.created_at.desc(), AnswerAttempt.id.desc())
        .limit(limit)
    )
    seen = set()
    word_ids = []
    for word_id in result.scalars():
        if word_id not in seen:
            seen.add(word_id)
            word_ids.append(word_id)
    return word_ids


async def mastered_word_ids(
    session: AsyncSession,
    user_id: int,
    task_type: str,
    direction: str,
    threshold: int = 5,
) -> list[int]:
    result = await session.execute(
        select(AnswerAttempt.word_id)
        .where(
            AnswerAttempt.user_id == user_id,
            AnswerAttempt.task_type == task_type,
            AnswerAttempt.direction == direction,
            AnswerAttempt.is_correct.is_(True),
        )
        .group_by(AnswerAttempt.word_id)
        .having(func.count(AnswerAttempt.id) >= threshold)
    )
    return list(result.scalars())


async def last_wrong_attempt(session: AsyncSession, user_id: int, word_id: int) -> AnswerAttempt | None:
    result = await session.execute(
        select(AnswerAttempt)
        .where(
            AnswerAttempt.user_id == user_id,
            AnswerAttempt.word_id == word_id,
            AnswerAttempt.is_correct.is_(False),
        )
        .order_by(AnswerAttempt.created_at.desc(), AnswerAttempt.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
