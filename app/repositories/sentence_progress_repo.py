from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SentenceProgress


async def get_or_create_sentence_progress(
    session: AsyncSession,
    user_id: int,
    sentence_id: str,
    task_type: str,
    direction: str,
) -> SentenceProgress:
    result = await session.execute(
        select(SentenceProgress).where(
            SentenceProgress.user_id == user_id,
            SentenceProgress.sentence_id == sentence_id,
            SentenceProgress.task_type == task_type,
            SentenceProgress.direction == direction,
        )
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        progress = SentenceProgress(
            user_id=user_id,
            sentence_id=sentence_id,
            task_type=task_type,
            direction=direction,
        )
        session.add(progress)
        await session.flush()
    return progress


async def record_sentence_answer(
    session: AsyncSession,
    user_id: int,
    sentence_id: str,
    task_type: str,
    direction: str,
    is_exact_correct: bool,
) -> SentenceProgress:
    progress = await get_or_create_sentence_progress(session, user_id, sentence_id, task_type, direction)
    if is_exact_correct:
        progress.correct_count += 1
        progress.correct_streak += 1
    else:
        progress.wrong_count += 1
        progress.correct_streak = 0
    progress.last_answer_at = datetime.now(timezone.utc)
    return progress


async def mastered_sentence_ids(
    session: AsyncSession,
    user_id: int,
    task_type: str,
    direction: str,
    threshold: int = 5,
) -> set[str]:
    result = await session.execute(
        select(SentenceProgress.sentence_id).where(
            SentenceProgress.user_id == user_id,
            SentenceProgress.task_type == task_type,
            SentenceProgress.direction == direction,
            SentenceProgress.correct_streak >= threshold,
        )
    )
    return set(result.scalars())
