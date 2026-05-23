import asyncio
import json
from pathlib import Path

from sqlalchemy import delete, select

from app.database import async_session_factory, create_db_schema
from app.models import AnswerAttempt, Topic, UserCurrentTask, UserWordProgress, Word, WordAnswer, WordExample
from app.services.import_service import import_words_from_json

WORDS_PATH = Path("data/words_a1.json")


async def sync_dictionary() -> None:
    if not WORDS_PATH.exists():
        raise FileNotFoundError(f"Dictionary file not found: {WORDS_PATH}")

    raw = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    wanted_slugs = {item["id"] for item in raw}

    await create_db_schema()
    async with async_session_factory() as session:
        stale_ids = select(Word.id).where((Word.level != "A1") | (~Word.slug.in_(wanted_slugs)))

        await session.execute(delete(UserCurrentTask).where(UserCurrentTask.word_id.in_(stale_ids)))
        await session.execute(delete(UserWordProgress).where(UserWordProgress.word_id.in_(stale_ids)))
        await session.execute(delete(AnswerAttempt).where(AnswerAttempt.word_id.in_(stale_ids)))
        await session.execute(delete(WordExample).where(WordExample.word_id.in_(stale_ids)))
        await session.execute(delete(WordAnswer).where(WordAnswer.word_id.in_(stale_ids)))
        await session.execute(delete(Word).where((Word.level != "A1") | (~Word.slug.in_(wanted_slugs))))

        imported = await import_words_from_json(session, WORDS_PATH)
        used_topic_ids = select(Word.topic_id)
        await session.execute(delete(Topic).where(~Topic.id.in_(used_topic_ids)))
        await session.commit()

        total = len(wanted_slugs)
        print(f"Dictionary synced: {total} A1 words, {imported} newly inserted.")


def main() -> None:
    asyncio.run(sync_dictionary())


if __name__ == "__main__":
    main()
