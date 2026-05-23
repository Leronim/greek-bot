from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import FSInputFile

from app.models import Word


AUDIO_DIR = Path("data/audio")
_transient_audio_messages: dict[tuple[int, int], set[int]] = {}


def word_audio_path(word: Word) -> Path:
    return AUDIO_DIR / f"{word.slug}.mp3"


def word_audio_exists(word: Word) -> bool:
    return word_audio_path(word).is_file()


def word_audio_file(word: Word) -> FSInputFile | None:
    path = word_audio_path(word)
    if not path.is_file():
        return None
    return FSInputFile(path, filename=f"{word.slug}.mp3")


def remember_transient_audio(chat_id: int, anchor_message_id: int, audio_message_id: int) -> None:
    key = (chat_id, anchor_message_id)
    _transient_audio_messages.setdefault(key, set()).add(audio_message_id)


async def delete_transient_audio(bot: Bot, chat_id: int, anchor_message_id: int) -> None:
    key = (chat_id, anchor_message_id)
    message_ids = _transient_audio_messages.pop(key, set())
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
