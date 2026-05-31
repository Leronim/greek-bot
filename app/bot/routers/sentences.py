from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.sentences import sentence_card_keyboard, sentence_result_keyboard
from app.models import User
from app.repositories.attempts_repo import touch_daily_activity
from app.services.sentences_service import Sentence, get_sentence, next_sentence_index, random_sentence_index

router = Router()


def sentence_card_text(sentence: Sentence) -> str:
    transcription = f"\n🔊 {sentence.transcription}" if sentence.transcription else ""
    return f"💬 Предложения\n\n🇬🇷 {sentence.greek}{transcription}"


def sentence_result_text(sentence: Sentence) -> str:
    transcription = f"\n🔊 {sentence.transcription}" if sentence.transcription else ""
    note = f"\n\n{sentence.note}" if sentence.note else ""
    return f"💬 Предложения\n\n🇬🇷 {sentence.greek}{transcription}\n🇷🇺 {sentence.ru}{note}"


@router.message(Command("sentences"))
async def sentences_command(message: Message, session: AsyncSession, db_user: User) -> None:
    await touch_daily_activity(session, db_user.id)
    index = random_sentence_index()
    if index is None:
        await message.answer("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
        return
    sentence = get_sentence(index)
    await message.answer(sentence_card_text(sentence), reply_markup=sentence_card_keyboard(index))


@router.callback_query(F.data == "sentences:start")
async def sentences_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await touch_daily_activity(session, db_user.id)
    index = random_sentence_index()
    if index is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    sentence = get_sentence(index)
    await callback.message.edit_text(sentence_card_text(sentence), reply_markup=sentence_card_keyboard(index))
    await callback.answer()


@router.callback_query(F.data.startswith("sentences:show:"))
async def sentences_show(callback: CallbackQuery) -> None:
    index = int(callback.data.rsplit(":", 1)[-1])
    sentence = get_sentence(index)
    if sentence is None:
        await callback.message.edit_text("Фраза не найдена.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(sentence_result_text(sentence), reply_markup=sentence_result_keyboard(index))
    await callback.answer()


@router.callback_query(F.data.startswith("sentences:next:"))
async def sentences_next(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await touch_daily_activity(session, db_user.id)
    current_index = int(callback.data.rsplit(":", 1)[-1])
    index = next_sentence_index(current_index)
    sentence = get_sentence(index)
    if sentence is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(sentence_card_text(sentence), reply_markup=sentence_card_keyboard(index))
    await callback.answer()
