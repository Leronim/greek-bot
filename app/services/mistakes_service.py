from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserCurrentTask, Word
from app.repositories import attempts_repo, progress_repo, settings_repo, words_repo
from app.services.progress_service import apply_answer_result
from app.services.typing_service import resolve_direction
from app.utils.normalize import normalize_answer


RECENT_MISTAKES_LIMIT = 12


async def choose_mistake_word(session: AsyncSession, user_id: int) -> Word | None:
    user_settings = await settings_repo.get_settings(session, user_id)
    recent_word_ids = await attempts_repo.recent_attempt_word_ids(
        session,
        user_id,
        task_type="mistakes",
        limit=RECENT_MISTAKES_LIMIT,
    )
    for exclude_word_ids in (recent_word_ids, []):
        word = await words_repo.get_mistake_word(
            session,
            user_id,
            user_settings.level_mode,
            exclude_word_ids=exclude_word_ids,
        )
        if word is not None:
            return word
    return None


async def create_mistake_task(
    session: AsyncSession,
    user_id: int,
    bot_message_id: int | None = None,
) -> tuple[Word | None, str | None]:
    user_settings = await settings_repo.get_settings(session, user_id)
    word = await choose_mistake_word(session, user_id)
    if word is None:
        return None, None
    direction = resolve_direction(user_settings.typing_direction)
    await progress_repo.set_current_task(session, user_id, "mistakes", word.id, direction, bot_message_id=bot_message_id)
    return word, direction


async def check_mistake_answer(
    session: AsyncSession,
    user_id: int,
    task: UserCurrentTask,
    user_answer: str,
) -> tuple[bool, Word]:
    word = await words_repo.get_word(session, task.word_id)
    if word is None:
        raise ValueError("Current task word does not exist")

    normalized = normalize_answer(user_answer, task.direction)
    answers = await words_repo.get_answers(session, task.word_id, task.direction)
    is_correct = normalized in {answer.normalized_answer for answer in answers}

    await attempts_repo.add_attempt(
        session,
        user_id=user_id,
        word_id=task.word_id,
        task_type="mistakes",
        direction=task.direction,
        user_answer=user_answer,
        is_correct=is_correct,
    )
    was_new = await apply_answer_result(session, user_id, task.word_id, is_correct)
    await attempts_repo.bump_daily_stats(session, user_id, is_correct=is_correct, is_new=was_new)
    await progress_repo.clear_current_task(session, user_id)
    return is_correct, word
