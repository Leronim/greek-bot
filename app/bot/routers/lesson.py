from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.lesson import lesson_card_keyboard, lesson_continue_keyboard, lesson_result_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models import User
from app.repositories import settings_repo, words_repo
from app.services.progress_service import mark_hard, mark_manual_result

router = Router()


def lesson_card_text(word) -> str:
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"📚 Урок\n\n🇬🇷 {word.greek}{transcription}\n\nПопробуй запомнить."


def lesson_answer_text(word) -> str:
    example = ""
    if word.examples:
        first = word.examples[0]
        example = f"\n\nПример:\n{first.example_el}\n{first.example_ru}"
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"🇬🇷 {word.greek}{transcription}\n🇷🇺 {word.ru}{example}"


@router.message(Command("lesson"))
async def lesson_command(message: Message, session: AsyncSession, db_user: User) -> None:
    await _send_lesson(message, session, db_user)


@router.callback_query(F.data == "lesson:start")
async def lesson_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    settings = await settings_repo.get_settings(session, db_user.id)
    word = await words_repo.get_new_word(session, db_user.id, settings.level_mode)
    if word is None:
        await callback.message.edit_text("Новых слов пока нет. Можно перейти к повторению.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(lesson_card_text(word), reply_markup=lesson_card_keyboard(word.id))
    await callback.answer()


async def _send_lesson(message: Message, session: AsyncSession, db_user: User) -> None:
    settings = await settings_repo.get_settings(session, db_user.id)
    word = await words_repo.get_new_word(session, db_user.id, settings.level_mode)
    if word is None:
        await message.answer("Новых слов пока нет. Можно перейти к повторению.", reply_markup=main_menu_keyboard())
    else:
        await message.answer(lesson_card_text(word), reply_markup=lesson_card_keyboard(word.id))


@router.callback_query(F.data.startswith("lesson:show:"))
async def lesson_show(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.message.edit_text("Слово не найдено.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(lesson_answer_text(word), reply_markup=lesson_result_keyboard(word.id))
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:knew:"))
async def lesson_knew(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    await mark_manual_result(session, db_user.id, word_id, knew=True)
    await callback.message.edit_text("✅ Отмечено как знакомое.", reply_markup=lesson_continue_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:hard:"))
async def lesson_hard(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    await mark_hard(session, db_user.id, word_id)
    await callback.message.edit_text("⭐ Добавлено в сложные.", reply_markup=lesson_continue_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:again:"))
async def lesson_again(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    await mark_manual_result(session, db_user.id, word_id, knew=False)
    await callback.message.edit_text("Слово вернётся на повторение позже.", reply_markup=lesson_continue_keyboard())
    await callback.answer()
