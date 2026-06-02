from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.mistakes import after_mistake_keyboard
from app.models import User
from app.repositories import progress_repo
from app.services import mistakes_service
from app.services.audio_service import delete_transient_audio, delete_transient_user_messages, remember_transient_user_message

router = Router()


def task_prompt(word, direction: str) -> str:
    if direction == "ru_to_el":
        return f"❌ Мои ошибки\n\nНапиши по-гречески:\n\n🇷🇺 {word.ru}"
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"❌ Мои ошибки\n\nПереведи на русский:\n\n🇬🇷 {word.greek}{transcription}"


def word_details(word) -> str:
    example = ""
    if word.examples:
        first = word.examples[0]
        example = f"\n\nПример:\n{first.example_el}\n{first.example_ru}"
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    return f"🇬🇷 {word.greek}{transcription}\n🇷🇺 {word.ru}{example}"


async def delete_bot_task_message(message: Message, task_message_id: int | None) -> None:
    if task_message_id is None:
        return
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=task_message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


@router.message(Command("mistakes"))
async def mistakes_command(message: Message, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.listening import clear_listening_task
    from app.bot.routers.sentences import clear_sentence_task

    clear_sentence_task(db_user.id)
    clear_listening_task(db_user.id)
    word, direction = await mistakes_service.create_mistake_task(session, db_user.id, bot_message_id=None)
    if word is None or direction is None:
        await message.answer("Пока нет ошибок для тренировки.", reply_markup=main_menu_keyboard())
        return
    sent = await message.answer(task_prompt(word, direction))
    await progress_repo.set_current_task(session, db_user.id, "mistakes", word.id, direction, bot_message_id=sent.message_id)


@router.callback_query(F.data == "mistakes:start")
async def mistakes_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.listening import clear_listening_task
    from app.bot.routers.sentences import clear_sentence_task

    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    clear_sentence_task(db_user.id)
    clear_listening_task(db_user.id)
    word, direction = await mistakes_service.create_mistake_task(
        session,
        db_user.id,
        bot_message_id=callback.message.message_id,
    )
    if word is None or direction is None:
        await callback.message.edit_text("Пока нет ошибок для тренировки.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(task_prompt(word, direction))
    await callback.answer()


@router.callback_query(F.data == "mistakes:next")
async def mistakes_next(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    word, direction = await mistakes_service.create_mistake_task(
        session,
        db_user.id,
        bot_message_id=callback.message.message_id,
    )
    if word is None or direction is None:
        await callback.message.edit_text("Пока нет ошибок для тренировки.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(task_prompt(word, direction))
    await callback.answer()


async def handle_text_answer(message: Message, session: AsyncSession, db_user: User) -> None:
    task = await progress_repo.get_current_task(session, db_user.id)
    user_answer = message.text or ""
    is_correct, word = await mistakes_service.check_mistake_answer(session, db_user.id, task, user_answer)
    await delete_bot_task_message(message, task.bot_message_id)
    if is_correct:
        result_message = await message.answer(
            f"✅ Верно!\n\n{word_details(word)}",
            reply_markup=after_mistake_keyboard(word.id),
        )
    else:
        result_message = await message.answer(
            f"❌ Неверно.\n\nПравильный ответ:\n{word_details(word)}",
            reply_markup=after_mistake_keyboard(word.id),
        )
    remember_transient_user_message(message.chat.id, result_message.message_id, message.message_id)
