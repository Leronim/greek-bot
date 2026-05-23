from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.quiz import after_quiz_keyboard, quiz_keyboard
from app.models import User
from app.repositories import words_repo
from app.services.quiz_service import apply_quiz_result, create_quiz

router = Router()


@router.message(Command("quiz"))
async def quiz_command(message: Message, session: AsyncSession, db_user: User) -> None:
    await _send_quiz_message(message, session, db_user)


@router.callback_query(F.data == "quiz:start")
async def quiz_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word, direction, options = await create_quiz(session, db_user.id)
    if word is None or direction is None:
        await callback.message.edit_text("Нет слов для теста.", reply_markup=main_menu_keyboard())
    else:
        correct = word.greek if direction == "ru_to_el" else word.ru
        if direction == "ru_to_el":
            text = f"Как будет по-гречески?\n\n🇷🇺 {word.ru}"
        else:
            transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
            text = f"Как переводится?\n\n🇬🇷 {word.greek}{transcription}"
        await callback.message.edit_text(text, reply_markup=quiz_keyboard(word.id, correct, options))
    await callback.answer()


async def _send_quiz_message(message: Message, session: AsyncSession, db_user: User) -> None:
    word, direction, options = await create_quiz(session, db_user.id)
    if word is None or direction is None:
        await message.answer("Нет слов для теста.", reply_markup=main_menu_keyboard())
        return
    correct = word.greek if direction == "ru_to_el" else word.ru
    text = f"Как будет по-гречески?\n\n🇷🇺 {word.ru}" if direction == "ru_to_el" else f"Как переводится?\n\n🇬🇷 {word.greek}"
    await message.answer(text, reply_markup=quiz_keyboard(word.id, correct, options))


@router.callback_query(F.data.startswith("quiz:answer:"))
async def quiz_answer(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    _, _, word_id_raw, marker = callback.data.split(":")
    word_id = int(word_id_raw)
    is_correct = marker == "1"
    await apply_quiz_result(session, db_user.id, word_id, is_correct)
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.message.edit_text("Слово не найдено.", reply_markup=main_menu_keyboard())
    elif is_correct:
        await callback.message.edit_text(f"✅ Верно!\n\n🇬🇷 {word.greek}\n🇷🇺 {word.ru}", reply_markup=after_quiz_keyboard(word.id))
    else:
        await callback.message.edit_text(
            f"❌ Неверно.\n\nПравильный ответ:\n🇬🇷 {word.greek}\n🇷🇺 {word.ru}",
            reply_markup=after_quiz_keyboard(word.id),
        )
    await callback.answer()
