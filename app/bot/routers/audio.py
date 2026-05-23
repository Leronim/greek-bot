from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import words_repo
from app.services.audio_service import word_audio_file

router = Router()


@router.callback_query(F.data.startswith("audio:word:"))
async def play_word_audio(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.answer("Слово не найдено", show_alert=True)
        return

    audio = word_audio_file(word)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    await callback.message.answer_audio(audio=audio, title=word.greek, performer="Greek TTS")
    await callback.answer()
