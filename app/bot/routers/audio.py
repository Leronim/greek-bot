from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import words_repo
from app.services.audio_service import remember_transient_audio, sentence_audio_file, word_audio_file
from app.services.sentences_service import get_sentence

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


@router.callback_query(F.data.startswith("audio:typing:word:"))
async def play_typing_word_audio(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.answer("Слово не найдено", show_alert=True)
        return

    audio = word_audio_file(word)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    audio_message = await callback.message.answer_audio(audio=audio, title=word.greek, performer="Greek TTS")
    remember_transient_audio(callback.message.chat.id, callback.message.message_id, audio_message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("audio:lesson:word:"))
async def play_lesson_word_audio(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.answer("Слово не найдено", show_alert=True)
        return

    audio = word_audio_file(word)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    audio_message = await callback.message.answer_audio(audio=audio, title=word.greek, performer="Greek TTS")
    remember_transient_audio(callback.message.chat.id, callback.message.message_id, audio_message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("audio:review:word:"))
async def play_review_word_audio(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.answer("Слово не найдено", show_alert=True)
        return

    audio = word_audio_file(word)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    audio_message = await callback.message.answer_audio(audio=audio, title=word.greek, performer="Greek TTS")
    remember_transient_audio(callback.message.chat.id, callback.message.message_id, audio_message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("audio:quiz:word:"))
async def play_quiz_word_audio(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.answer("Слово не найдено", show_alert=True)
        return

    audio = word_audio_file(word)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    audio_message = await callback.message.answer_audio(audio=audio, title=word.greek, performer="Greek TTS")
    remember_transient_audio(callback.message.chat.id, callback.message.message_id, audio_message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("audio:sentence:"))
async def play_sentence_audio(callback: CallbackQuery) -> None:
    index = int(callback.data.rsplit(":", 1)[-1])
    sentence = get_sentence(index)
    if sentence is None:
        await callback.answer("Фраза не найдена", show_alert=True)
        return

    audio = sentence_audio_file(sentence)
    if audio is None:
        await callback.answer("Аудио ещё не создано", show_alert=True)
        return

    audio_message = await callback.message.answer_audio(audio=audio, title=sentence.greek, performer="Greek TTS")
    remember_transient_audio(callback.message.chat.id, callback.message.message_id, audio_message.message_id)
    await callback.answer()
