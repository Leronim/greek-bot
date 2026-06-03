from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.sentences import sentence_result_keyboard, sentence_task_keyboard
from app.models import User
from app.repositories import attempts_repo, progress_repo
from app.services.audio_service import delete_transient_audio, delete_transient_user_messages, remember_transient_user_message
from app.services.sentences_service import (
    Sentence,
    check_sentence_answer,
    get_sentence,
    random_next_sentence_index,
    random_sentence_index,
)

router = Router()
_sentence_tasks: dict[int, tuple[int, int | None]] = {}


def clear_sentence_task(user_id: int) -> None:
    _sentence_tasks.pop(user_id, None)


def has_sentence_task(user_id: int) -> bool:
    return user_id in _sentence_tasks


def sentence_task_text(sentence: Sentence) -> str:
    return f"💬 Напиши по-гречески:\n\n🇷🇺 {sentence.ru}"


def sentence_result_text(sentence: Sentence) -> str:
    transcription = f"\n🔊 {sentence.transcription}" if sentence.transcription else ""
    note = f"\n\n{sentence.note}" if sentence.note else ""
    return f"🇬🇷 {sentence.greek}{transcription}\n🇷🇺 {sentence.ru}{note}"


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


async def create_sentence_task(
    session: AsyncSession,
    user_id: int,
    bot_message_id: int | None,
    index: int | None = None,
) -> tuple[int | None, Sentence | None]:
    if index is None:
        index = random_sentence_index()
    if index is None:
        return None, None
    sentence = get_sentence(index)
    if sentence is None:
        return None, None
    _sentence_tasks[user_id] = (index, bot_message_id)
    await attempts_repo.touch_daily_activity(session, user_id)
    return index, sentence


@router.message(Command("sentences"))
async def sentences_command(message: Message, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.listening import clear_listening_task

    clear_listening_task(db_user.id)
    await progress_repo.clear_current_task(session, db_user.id)
    index, sentence = await create_sentence_task(session, db_user.id, bot_message_id=None)
    if sentence is None or index is None:
        await message.answer("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
        return
    sent = await message.answer(sentence_task_text(sentence), reply_markup=sentence_task_keyboard(index))
    _sentence_tasks[db_user.id] = (index, sent.message_id)


@router.callback_query(F.data == "sentences:start")
async def sentences_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.listening import clear_listening_task

    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    clear_listening_task(db_user.id)
    await progress_repo.clear_current_task(session, db_user.id)
    index, sentence = await create_sentence_task(session, db_user.id, bot_message_id=callback.message.message_id)
    if sentence is None or index is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(sentence_task_text(sentence), reply_markup=sentence_task_keyboard(index))
    await callback.answer()


@router.callback_query(F.data.startswith("sentences:show:"))
async def sentences_show(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    index = int(callback.data.rsplit(":", 1)[-1])
    sentence = get_sentence(index)
    _sentence_tasks.pop(db_user.id, None)
    if sentence is None:
        await callback.message.edit_text("Фраза не найдена.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(
            f"Правильный ответ:\n\n{sentence_result_text(sentence)}",
            reply_markup=sentence_result_keyboard(index),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sentences:next:"))
async def sentences_next(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    current_index = int(callback.data.rsplit(":", 1)[-1])
    index = random_next_sentence_index(current_index)
    index, sentence = await create_sentence_task(
        session,
        db_user.id,
        bot_message_id=callback.message.message_id,
        index=index,
    )
    if sentence is None or index is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(sentence_task_text(sentence), reply_markup=sentence_task_keyboard(index))
    await callback.answer()


async def handle_sentence_answer(message: Message, session: AsyncSession, db_user: User) -> None:
    task = _sentence_tasks.get(db_user.id)
    if task is None:
        return
    index, bot_message_id = task

    sentence = get_sentence(index)
    if sentence is None:
        _sentence_tasks.pop(db_user.id, None)
        await message.answer("Фраза не найдена.", reply_markup=main_menu_keyboard())
        return

    answer_check = check_sentence_answer(sentence, message.text or "")
    await attempts_repo.touch_daily_activity(session, db_user.id)
    _sentence_tasks.pop(db_user.id, None)
    await delete_bot_task_message(message, bot_message_id)

    if answer_check.is_correct:
        result_message = await message.answer(
            f"✅ Верно!\n\n{sentence_result_text(sentence)}",
            reply_markup=sentence_result_keyboard(index),
        )
        remember_transient_user_message(message.chat.id, result_message.message_id, message.message_id)
        return

    if answer_check.is_almost:
        result_message = await message.answer(
            "🟡 Почти верно.\n\n"
            f"Твой ответ:\n{message.text or ''}\n\n"
            f"Правильно:\n{sentence_result_text(sentence)}",
            reply_markup=sentence_result_keyboard(index),
        )
        remember_transient_user_message(message.chat.id, result_message.message_id, message.message_id)
        return

    result_message = await message.answer(
        f"❌ Неверно.\n\nПравильный ответ:\n{sentence_result_text(sentence)}",
        reply_markup=sentence_result_keyboard(index),
    )
    remember_transient_user_message(message.chat.id, result_message.message_id, message.message_id)
