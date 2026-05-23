from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserCurrentTask, UserWordProgress
from app.utils.time import utcnow


async def get_progress(session: AsyncSession, user_id: int, word_id: int) -> UserWordProgress | None:
    result = await session.execute(
        select(UserWordProgress).where(UserWordProgress.user_id == user_id, UserWordProgress.word_id == word_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_progress(session: AsyncSession, user_id: int, word_id: int) -> UserWordProgress:
    progress = await get_progress(session, user_id, word_id)
    if progress is None:
        progress = UserWordProgress(user_id=user_id, word_id=word_id, box=0)
        session.add(progress)
        await session.flush()
    return progress


async def get_current_task(session: AsyncSession, user_id: int) -> UserCurrentTask | None:
    result = await session.execute(select(UserCurrentTask).where(UserCurrentTask.user_id == user_id))
    return result.scalar_one_or_none()


async def set_current_task(
    session: AsyncSession,
    user_id: int,
    task_type: str,
    word_id: int,
    direction: str,
    bot_message_id: int | None = None,
) -> UserCurrentTask:
    current = await get_current_task(session, user_id)
    if current is None:
        current = UserCurrentTask(
            user_id=user_id,
            task_type=task_type,
            word_id=word_id,
            direction=direction,
            bot_message_id=bot_message_id,
        )
        session.add(current)
    else:
        current.task_type = task_type
        current.word_id = word_id
        current.direction = direction
        current.bot_message_id = bot_message_id
    await session.flush()
    return current


async def clear_current_task(session: AsyncSession, user_id: int) -> None:
    current = await get_current_task(session, user_id)
    if current is not None:
        await session.delete(current)
        await session.flush()


async def count_due_reviews(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count(UserWordProgress.id)).where(
            UserWordProgress.user_id == user_id,
            UserWordProgress.next_review_at <= utcnow(),
        )
    )
    return result.scalar_one()
