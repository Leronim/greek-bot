import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sentence_progress_repo import mastered_sentence_ids
from app.services.sentences_service import load_sentences


SENTENCE_MASTERY_THRESHOLD = 5
MASTERED_SENTENCE_CHANCE = 0.15


async def choose_sentence_index(
    session: AsyncSession,
    user_id: int,
    task_type: str,
    direction: str,
    exclude_index: int | None = None,
) -> int | None:
    sentences = load_sentences()
    if not sentences:
        return None

    mastered_ids = await mastered_sentence_ids(
        session,
        user_id,
        task_type=task_type,
        direction=direction,
        threshold=SENTENCE_MASTERY_THRESHOLD,
    )
    indexes = [index for index in range(len(sentences)) if index != exclude_index]
    if not indexes:
        return 0

    non_mastered = [index for index in indexes if sentences[index].id not in mastered_ids]
    mastered = [index for index in indexes if sentences[index].id in mastered_ids]

    if non_mastered and (not mastered or random.random() >= MASTERED_SENTENCE_CHANCE):
        return random.choice(non_mastered)
    if mastered:
        return random.choice(mastered)
    return random.choice(indexes)
