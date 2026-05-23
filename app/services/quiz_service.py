import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Word
from app.repositories import attempts_repo, settings_repo, words_repo
from app.services.progress_service import apply_answer_result


async def create_quiz(session: AsyncSession, user_id: int) -> tuple[Word | None, str | None, list[str]]:
    user_settings = await settings_repo.get_settings(session, user_id)
    word = await words_repo.get_due_word(session, user_id, user_settings.level_mode)
    if word is None:
        word = await words_repo.get_new_word(session, user_id, user_settings.level_mode)
    if word is None:
        word = await words_repo.get_random_word(session, user_id, user_settings.level_mode)
    if word is None:
        return None, None, []
    direction = random.choice(["ru_to_el", "el_to_ru"])
    options = await words_repo.get_quiz_options(session, word, direction, user_settings.level_mode)
    random.shuffle(options)
    return word, direction, options


async def apply_quiz_result(session: AsyncSession, user_id: int, word_id: int, is_correct: bool) -> None:
    was_new = await apply_answer_result(session, user_id, word_id, is_correct)
    await attempts_repo.bump_daily_stats(session, user_id, is_correct=is_correct, is_new=was_new)
