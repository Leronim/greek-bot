import argparse
import asyncio

import edge_tts
from sqlalchemy import select

from app.database import async_session_factory
from app.models import Word
from app.services.audio_service import AUDIO_DIR, sentence_audio_path, word_audio_path
from app.services.sentences_service import load_sentences


DEFAULT_VOICE = "el-GR-AthinaNeural"


async def generate_audio(voice: str, overwrite: bool, limit: int | None) -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIO_DIR / "sentences").mkdir(parents=True, exist_ok=True)

    async with async_session_factory() as session:
        result = await session.execute(select(Word).where(Word.is_active.is_(True)).order_by(Word.slug))
        words = result.scalars().all()

    generated = 0
    skipped = 0
    for word in words:
        if limit is not None and generated >= limit:
            break

        path = word_audio_path(word)
        if path.exists() and not overwrite:
            skipped += 1
            continue

        communicate = edge_tts.Communicate(word.greek, voice)
        await communicate.save(str(path))
        generated += 1
        print(f"generated {path}")

    sentence_generated = 0
    sentence_skipped = 0
    for sentence in load_sentences():
        if limit is not None and generated + sentence_generated >= limit:
            break

        path = sentence_audio_path(sentence)
        if path.exists() and not overwrite:
            sentence_skipped += 1
            continue

        communicate = edge_tts.Communicate(sentence.greek, voice)
        await communicate.save(str(path))
        sentence_generated += 1
        print(f"generated {path}")

    print(
        "Audio ready: "
        f"{generated} words generated, {skipped} words skipped; "
        f"{sentence_generated} sentences generated, {sentence_skipped} sentences skipped."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Greek pronunciation audio files for active words.")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(generate_audio(args.voice, args.overwrite, args.limit))


if __name__ == "__main__":
    main()
