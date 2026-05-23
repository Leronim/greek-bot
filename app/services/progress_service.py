from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.progress_repo import get_or_create_progress
from app.utils.time import utcnow

BOX_INTERVALS = {
    1: timedelta(minutes=30),
    2: timedelta(days=1),
    3: timedelta(days=3),
    4: timedelta(days=7),
    5: timedelta(days=14),
    6: timedelta(days=30),
}


async def apply_answer_result(session: AsyncSession, user_id: int, word_id: int, is_correct: bool) -> bool:
    progress = await get_or_create_progress(session, user_id, word_id)
    was_new = progress.correct_count == 0 and progress.wrong_count == 0
    now = utcnow()

    if is_correct:
        progress.correct_count += 1
        progress.box = min(progress.box + 1, 6)
        progress.next_review_at = now + BOX_INTERVALS[progress.box]
        progress.is_learned = progress.box >= 6
    else:
        progress.wrong_count += 1
        progress.box = 1
        progress.next_review_at = now + BOX_INTERVALS[1]
        progress.is_hard = progress.wrong_count >= 3
        progress.is_learned = False

    progress.last_answer_at = now
    return was_new


async def mark_manual_result(session: AsyncSession, user_id: int, word_id: int, knew: bool) -> None:
    await apply_answer_result(session, user_id, word_id, knew)


async def mark_hard(session: AsyncSession, user_id: int, word_id: int) -> None:
    progress = await get_or_create_progress(session, user_id, word_id)
    progress.is_hard = True
    progress.box = max(progress.box, 1)
    progress.next_review_at = utcnow() + BOX_INTERVALS[1]
