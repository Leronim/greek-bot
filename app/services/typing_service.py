import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserCurrentTask, Word
from app.repositories import attempts_repo, progress_repo, settings_repo, words_repo
from app.services.progress_service import apply_answer_result
from app.utils.normalize import normalize_answer


def resolve_direction(mode: str) -> str:
    if mode in {"ru_to_el", "el_to_ru"}:
        return mode
    return random.choice(["ru_to_el", "el_to_ru"])


RECENT_TYPING_LIMIT = 35
NEW_WORD_CHANCE = 0.55
WORD_MASTERY_THRESHOLD = 5
MASTERED_WORD_CHANCE = 0.15


def merge_exclude_ids(*groups: list[int]) -> list[int]:
    merged: list[int] = []
    seen: set[int] = set()
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


async def choose_training_word(
    session: AsyncSession,
    user_id: int,
    direction: str,
    hard_only: bool = False,
) -> Word | None:
    user_settings = await settings_repo.get_settings(session, user_id)
    recent_word_ids = await attempts_repo.recent_attempt_word_ids(
        session,
        user_id,
        task_type="typing",
        limit=RECENT_TYPING_LIMIT,
    )
    mastered_word_ids = await attempts_repo.mastered_word_ids(
        session,
        user_id,
        task_type="typing",
        direction=direction,
        threshold=WORD_MASTERY_THRESHOLD,
    )
    mastered_exclude_ids = [] if random.random() < MASTERED_WORD_CHANCE else mastered_word_ids
    exclude_groups = (
        merge_exclude_ids(recent_word_ids, mastered_exclude_ids),
        mastered_exclude_ids,
        recent_word_ids,
        [],
    )

    if hard_only:
        for exclude_word_ids in exclude_groups:
            word = await words_repo.get_due_word(
                session,
                user_id,
                user_settings.level_mode,
                hard_only=True,
                exclude_word_ids=exclude_word_ids,
            )
            if word is not None:
                return word
        return None

    for exclude_word_ids in exclude_groups:
        prefer_new = random.random() < NEW_WORD_CHANCE
        strategies = (
            ("new", "random", "due")
            if prefer_new
            else ("random", "new", "due")
        )

        for strategy in strategies:
            if strategy == "new":
                word = await words_repo.get_new_word(
                    session,
                    user_id,
                    user_settings.level_mode,
                    exclude_word_ids=exclude_word_ids,
                )
            elif strategy == "due":
                word = await words_repo.get_due_word(
                    session,
                    user_id,
                    user_settings.level_mode,
                    exclude_word_ids=exclude_word_ids,
                )
            else:
                word = await words_repo.get_random_word(
                    session,
                    user_id,
                    user_settings.level_mode,
                    exclude_word_ids=exclude_word_ids,
                )

            if word is not None:
                return word

    return None


async def create_typing_task(
    session: AsyncSession,
    user_id: int,
    direction: str | None = None,
    hard_only: bool = False,
    bot_message_id: int | None = None,
) -> tuple[Word | None, str | None]:
    user_settings = await settings_repo.get_settings(session, user_id)
    direction = direction or resolve_direction(user_settings.typing_direction)
    word = await choose_training_word(session, user_id, direction=direction, hard_only=hard_only)
    if word is None:
        return None, None
    await progress_repo.set_current_task(session, user_id, "typing", word.id, direction, bot_message_id=bot_message_id)
    return word, direction


async def check_typing_answer(
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
        task_type="typing",
        direction=task.direction,
        user_answer=user_answer,
        is_correct=is_correct,
    )
    was_new = await apply_answer_result(session, user_id, task.word_id, is_correct)
    await attempts_repo.bump_daily_stats(session, user_id, is_correct=is_correct, is_new=was_new)
    await progress_repo.clear_current_task(session, user_id)
    return is_correct, word
