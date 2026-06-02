from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AnswerAttempt, Topic, UserWordProgress, Word, WordAnswer
from app.utils.time import utcnow


def levels_for_mode(level_mode: str) -> list[str]:
    return ["A1"]


async def count_words(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Word.id)).where(Word.is_active.is_(True)))
    return result.scalar_one()


async def get_word(session: AsyncSession, word_id: int) -> Word | None:
    result = await session.execute(
        select(Word)
        .options(selectinload(Word.answers), selectinload(Word.examples), selectinload(Word.topic))
        .where(Word.id == word_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_topic(session: AsyncSession, level: str, title: str) -> Topic:
    slug = f"{level.lower()}-{title.lower().replace(' ', '-')}"
    result = await session.execute(select(Topic).where(Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if topic is None:
        topic = Topic(level=level, title=title, slug=slug)
        session.add(topic)
        await session.flush()
    return topic


async def get_due_word(
    session: AsyncSession,
    user_id: int,
    level_mode: str,
    hard_only: bool = False,
    exclude_word_ids: list[int] | None = None,
) -> Word | None:
    levels = levels_for_mode(level_mode)
    query = (
        select(Word)
        .join(UserWordProgress, UserWordProgress.word_id == Word.id)
        .options(selectinload(Word.answers), selectinload(Word.examples), selectinload(Word.topic))
        .where(
            UserWordProgress.user_id == user_id,
            Word.is_active.is_(True),
            Word.level.in_(levels),
            UserWordProgress.next_review_at <= utcnow(),
        )
        .order_by(UserWordProgress.is_hard.desc(), UserWordProgress.next_review_at.asc())
        .limit(1)
    )
    if hard_only:
        query = query.where(UserWordProgress.is_hard.is_(True))
    if exclude_word_ids:
        query = query.where(~Word.id.in_(exclude_word_ids))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_new_word(
    session: AsyncSession,
    user_id: int,
    level_mode: str,
    exclude_word_ids: list[int] | None = None,
) -> Word | None:
    levels = levels_for_mode(level_mode)
    query = (
        select(Word)
        .options(selectinload(Word.answers), selectinload(Word.examples), selectinload(Word.topic))
        .outerjoin(
            UserWordProgress,
            (UserWordProgress.word_id == Word.id) & (UserWordProgress.user_id == user_id),
        )
        .where(
            Word.is_active.is_(True),
            Word.level.in_(levels),
            UserWordProgress.id.is_(None),
        )
        .order_by(func.random())
        .limit(1)
    )
    if exclude_word_ids:
        query = query.where(~Word.id.in_(exclude_word_ids))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_random_word(
    session: AsyncSession,
    user_id: int,
    level_mode: str,
    exclude_word_ids: list[int] | None = None,
) -> Word | None:
    levels = levels_for_mode(level_mode)
    query = (
        select(Word)
        .options(selectinload(Word.answers), selectinload(Word.examples), selectinload(Word.topic))
        .where(Word.is_active.is_(True), Word.level.in_(levels))
        .order_by(func.random())
        .limit(1)
    )
    if exclude_word_ids:
        query = query.where(~Word.id.in_(exclude_word_ids))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_mistake_word(
    session: AsyncSession,
    user_id: int,
    level_mode: str,
    exclude_word_ids: list[int] | None = None,
) -> Word | None:
    levels = levels_for_mode(level_mode)
    wrong_count = func.count(AnswerAttempt.id)
    query = (
        select(Word)
        .join(AnswerAttempt, AnswerAttempt.word_id == Word.id)
        .options(selectinload(Word.answers), selectinload(Word.examples), selectinload(Word.topic))
        .where(
            AnswerAttempt.user_id == user_id,
            AnswerAttempt.is_correct.is_(False),
            Word.is_active.is_(True),
            Word.level.in_(levels),
        )
        .group_by(Word.id)
        .order_by(wrong_count.desc(), func.random())
        .limit(1)
    )
    if exclude_word_ids:
        query = query.where(~Word.id.in_(exclude_word_ids))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_answers(session: AsyncSession, word_id: int, direction: str) -> list[WordAnswer]:
    result = await session.execute(
        select(WordAnswer).where(WordAnswer.word_id == word_id, WordAnswer.direction == direction)
    )
    return list(result.scalars())


async def get_quiz_options(session: AsyncSession, word: Word, direction: str, level_mode: str) -> list[str]:
    levels = levels_for_mode(level_mode)
    target = word.greek if direction == "ru_to_el" else word.ru
    option_field = Word.greek if direction == "ru_to_el" else Word.ru
    result = await session.execute(
        select(option_field)
        .where(Word.id != word.id, Word.is_active.is_(True), Word.level.in_(levels))
        .order_by(func.random())
        .limit(3)
    )
    options = [target, *result.scalars().all()]
    return options


async def find_word_by_slug(session: AsyncSession, slug: str) -> Word | None:
    result = await session.execute(select(Word).where(Word.slug == slug))
    return result.scalar_one_or_none()
