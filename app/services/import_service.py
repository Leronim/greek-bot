import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Word, WordAnswer, WordExample
from app.repositories.words_repo import count_words, find_word_by_slug, get_or_create_topic
from app.utils.normalize import normalize_greek, normalize_russian


async def import_words_if_empty(session: AsyncSession, paths: list[Path]) -> int:
    if await count_words(session) > 0:
        return 0
    imported = 0
    for path in paths:
        if path.exists():
            imported += await import_words_from_json(session, path)
    return imported


async def import_words_from_json(session: AsyncSession, path: Path) -> int:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Words JSON must contain a list")

    imported = 0
    for item in raw:
        imported += await upsert_word(session, item)
    return imported


async def upsert_word(session: AsyncSession, item: dict[str, Any]) -> int:
    slug = item["id"]
    existing = await find_word_by_slug(session, slug)
    topic = await get_or_create_topic(session, item["level"], item["topic"])
    lessons = _serialize_lessons(item)

    if existing is None:
        word = Word(
            slug=slug,
            level=item["level"],
            topic_id=topic.id,
            greek=item["greek"],
            transcription=item.get("transcription"),
            ru=item["ru"],
            part_of_speech=item.get("part_of_speech"),
            gender=item.get("gender"),
            lesson=item.get("lesson"),
            lessons=lessons,
            is_active=item.get("is_active", True),
        )
        session.add(word)
        await session.flush()
        imported = 1
    else:
        word = existing
        word.level = item["level"]
        word.topic_id = topic.id
        word.greek = item["greek"]
        word.transcription = item.get("transcription")
        word.ru = item["ru"]
        word.part_of_speech = item.get("part_of_speech")
        word.gender = item.get("gender")
        word.lesson = item.get("lesson")
        word.lessons = lessons
        word.is_active = item.get("is_active", True)
        imported = 0

    await _replace_answers(session, word, item)
    await _replace_examples(session, word, item)
    return imported


def _serialize_lessons(item: dict[str, Any]) -> str | None:
    lessons: list[str] = []
    lesson = item.get("lesson")
    if lesson:
        lessons.append(lesson)
    for value in item.get("lessons") or []:
        if value not in lessons:
            lessons.append(value)
    return json.dumps(lessons, ensure_ascii=False) if lessons else None


async def _replace_answers(session: AsyncSession, word: Word, item: dict[str, Any]) -> None:
    existing = await session.execute(select(WordAnswer).where(WordAnswer.word_id == word.id))
    for answer in existing.scalars():
        await session.delete(answer)
    await session.flush()

    greek_answers = _unique_normalized_answers(
        [item["greek"], *(item.get("greek_answers") or [])],
        normalize_greek,
    )
    ru_answers = _unique_normalized_answers(
        [item["ru"], *(item.get("ru_answers") or [])],
        normalize_russian,
    )

    for answer, normalized in greek_answers:
        session.add(
            WordAnswer(
                word_id=word.id,
                direction="ru_to_el",
                answer=answer,
                normalized_answer=normalized,
            )
        )
    for answer, normalized in ru_answers:
        session.add(
            WordAnswer(
                word_id=word.id,
                direction="el_to_ru",
                answer=answer,
                normalized_answer=normalized,
            )
        )


def _unique_normalized_answers(answers: list[str], normalize) -> list[tuple[str, str]]:
    unique: dict[str, str] = {}
    for answer in answers:
        normalized = normalize(answer)
        if normalized and normalized not in unique:
            unique[normalized] = answer
    return [(answer, normalized) for normalized, answer in unique.items()]


async def _replace_examples(session: AsyncSession, word: Word, item: dict[str, Any]) -> None:
    existing = await session.execute(select(WordExample).where(WordExample.word_id == word.id))
    for example in existing.scalars():
        await session.delete(example)
    await session.flush()

    if item.get("example_el") and item.get("example_ru"):
        session.add(
            WordExample(
                word_id=word.id,
                example_el=item["example_el"],
                example_ru=item["example_ru"],
                sort_order=0,
            )
        )
