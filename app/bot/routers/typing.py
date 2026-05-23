from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.typing import after_typing_keyboard, typing_mode_keyboard
from app.models import User
from app.repositories import progress_repo, words_repo
from app.services.audio_service import delete_transient_audio
from app.services import typing_service

router = Router()


def task_prompt(word, direction: str) -> str:
    if direction == "ru_to_el":
        return f"✍️ Напиши по-гречески:\n\n🇷🇺 {word.ru}"
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"✍️ Переведи на русский:\n\n🇬🇷 {word.greek}{transcription}"


def word_details(word) -> str:
    example = ""
    if word.examples:
        first = word.examples[0]
        example = f"\n\nПример:\n{first.example_el}\n{first.example_ru}"
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"🇬🇷 {word.greek}{transcription}\n🇷🇺 {word.ru}{example}"


async def delete_user_answer(message: Message) -> None:
    try:
        await message.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def delete_bot_task_message(message: Message, task_message_id: int | None) -> None:
    if task_message_id is None:
        return
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=task_message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


@router.message(Command("typing"))
async def typing_command(message: Message) -> None:
    await message.answer("✍️ Написать ответ\n\nВыбери режим:", reply_markup=typing_mode_keyboard())


@router.callback_query(F.data == "typing:menu")
async def typing_menu(callback: CallbackQuery) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await callback.message.edit_text("✍️ Написать ответ\n\nВыбери режим:", reply_markup=typing_mode_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("typing:start:"))
async def typing_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    mode = callback.data.rsplit(":", 1)[-1]
    direction = None if mode == "mixed" else mode
    word, resolved_direction = await typing_service.create_typing_task(
        session,
        db_user.id,
        direction=direction,
        bot_message_id=callback.message.message_id,
    )
    if word is None or resolved_direction is None:
        await callback.message.edit_text("Пока нет доступных слов. Добавь слова через импорт.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(task_prompt(word, resolved_direction))
    await callback.answer()


@router.callback_query(F.data == "typing:next")
async def typing_next(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    word, direction = await typing_service.create_typing_task(
        session,
        db_user.id,
        bot_message_id=callback.message.message_id,
    )
    if word is None or direction is None:
        await callback.message.edit_text("Нет слов для тренировки.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(task_prompt(word, direction))
    await callback.answer()


@router.callback_query(F.data.startswith("typing:example"))
async def typing_example(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    parts = callback.data.split(":")
    word_id = int(parts[2]) if len(parts) == 3 else None
    task = await progress_repo.get_current_task(session, db_user.id) if word_id is None else None
    if word_id is None and task is None:
        await callback.message.edit_text("Сейчас нет активного задания.", reply_markup=main_menu_keyboard())
    else:
        word = await words_repo.get_word(session, word_id or task.word_id)
        if word is None:
            await callback.message.edit_text("Слово не найдено.", reply_markup=main_menu_keyboard())
        else:
            await callback.message.edit_text(word_details(word), reply_markup=after_typing_keyboard(word.id))
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_answer(message: Message, session: AsyncSession, db_user: User) -> None:
    task = await progress_repo.get_current_task(session, db_user.id)
    if task is None or task.task_type != "typing":
        await message.answer("Выбери режим в меню, и я дам задание.", reply_markup=main_menu_keyboard())
        return

    user_answer = message.text or ""
    is_correct, word = await typing_service.check_typing_answer(session, db_user.id, task, user_answer)
    await delete_user_answer(message)
    await delete_bot_task_message(message, task.bot_message_id)
    if is_correct:
        await message.answer(f"✅ Верно!\n\n{word_details(word)}", reply_markup=after_typing_keyboard(word.id))
        return

    await message.answer(
        f"❌ Неверно.\n\nПравильный ответ:\n{word_details(word)}",
        reply_markup=after_typing_keyboard(word.id),
    )
