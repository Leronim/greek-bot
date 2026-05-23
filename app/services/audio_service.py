from pathlib import Path

from aiogram.types import FSInputFile

from app.models import Word


AUDIO_DIR = Path("data/audio")


def word_audio_path(word: Word) -> Path:
    return AUDIO_DIR / f"{word.slug}.mp3"


def word_audio_exists(word: Word) -> bool:
    return word_audio_path(word).is_file()


def word_audio_file(word: Word) -> FSInputFile | None:
    path = word_audio_path(word)
    if not path.is_file():
        return None
    return FSInputFile(path, filename=f"{word.slug}.mp3")
