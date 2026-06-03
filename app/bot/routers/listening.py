from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.listening import listening_result_keyboard, listening_task_keyboard
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models import User
from app.repositories import attempts_repo, progress_repo
from app.services.audio_service import (
    delete_transient_audio,
    delete_transient_user_messages,
    remember_transient_audio,
    remember_transient_user_message,
    sentence_audio_file,
)
from app.services.sentences_service import (
    Sentence,
    check_sentence_answer,
    get_sentence,
    random_next_sentence_index,
    random_sentence_index,
)

router = Router()
_listening_tasks: dict[int, tuple[int, int | None]] = {}


def clear_listening_task(user_id: int) -> None:
    _listening_tasks.pop(user_id, None)


def has_listening_task(user_id: int) -> bool:
    return user_id in _listening_tasks


def listening_task_text() -> str:
    return "👂 Аудирование\n\nПослушай фразу и напиши её по-гречески."


def listening_result_text(sentence: Sentence) -> str:
    transcription = f"\n🔊 {sentence.transcription}" if sentence.transcription else ""
    note = f"\n\n{sentence.note}" if sentence.note else ""
    return f"🇬🇷 {sentence.greek}{transcription}\n🇷🇺 {sentence.ru}{note}"


async def delete_bot_task_message(message: Message, task_message_id: int | None) -> None:
    if task_message_id is None:
        return
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=task_message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def send_sentence_audio(message: Message, sentence: Sentence, anchor_message_id: int) -> None:
    audio = sentence_audio_file(sentence)
    if audio is None:
        await message.answer("Аудио для этой фразы ещё не создано.")
        return
    audio_message = await message.answer_audio(audio=audio, title="Аудирование", performer="Greek TTS")
    remember_transient_audio(message.chat.id, anchor_message_id, audio_message.message_id)


async def create_listening_task(
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
    _listening_tasks[user_id] = (index, bot_message_id)
    await attempts_repo.touch_daily_activity(session, user_id)
    return index, sentence


@router.message(Command("listening"))
async def listening_command(message: Message, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.sentences import clear_sentence_task

    clear_sentence_task(db_user.id)
    await progress_repo.clear_current_task(session, db_user.id)
    index, sentence = await create_listening_task(session, db_user.id, bot_message_id=None)
    if sentence is None or index is None:
        await message.answer("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
        return
    sent = await message.answer(listening_task_text(), reply_markup=listening_task_keyboard(index))
    _listening_tasks[db_user.id] = (index, sent.message_id)
    await send_sentence_audio(sent, sentence, sent.message_id)


@router.callback_query(F.data == "listening:start")
async def listening_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    from app.bot.routers.sentences import clear_sentence_task

    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    clear_sentence_task(db_user.id)
    await progress_repo.clear_current_task(session, db_user.id)
    index, sentence = await create_listening_task(session, db_user.id, bot_message_id=callback.message.message_id)
    if sentence is None or index is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(listening_task_text(), reply_markup=listening_task_keyboard(index))
        await send_sentence_audio(callback.message, sentence, callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("listening:show:"))
async def listening_show(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    index = int(callback.data.rsplit(":", 1)[-1])
    sentence = get_sentence(index)
    _listening_tasks.pop(db_user.id, None)
    if sentence is None:
        await callback.message.edit_text("Фраза не найдена.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(
            f"Правильный ответ:\n\n{listening_result_text(sentence)}",
            reply_markup=listening_result_keyboard(index),
        )
    await attempts_repo.touch_daily_activity(session, db_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("listening:next:"))
async def listening_next(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    current_index = int(callback.data.rsplit(":", 1)[-1])
    index = random_next_sentence_index(current_index)
    index, sentence = await create_listening_task(
        session,
        db_user.id,
        bot_message_id=callback.message.message_id,
        index=index,
    )
    if sentence is None or index is None:
        await callback.message.edit_text("Словарь предложений пока пуст.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(listening_task_text(), reply_markup=listening_task_keyboard(index))
        await send_sentence_audio(callback.message, sentence, callback.message.message_id)
    await callback.answer()


async def handle_listening_answer(message: Message, session: AsyncSession, db_user: User) -> None:
    task = _listening_tasks.get(db_user.id)
    if task is None:
        return
    index, bot_message_id = task

    sentence = get_sentence(index)
    if sentence is None:
        _listening_tasks.pop(db_user.id, None)
        await message.answer("Фраза не найдена.", reply_markup=main_menu_keyboard())
        return

    answer_check = check_sentence_answer(sentence, message.text or "")
    await attempts_repo.touch_daily_activity(session, db_user.id)
    _listening_tasks.pop(db_user.id, None)
    await delete_bot_task_message(message, bot_message_id)
    if bot_message_id is not None:
        await delete_transient_audio(message.bot, message.chat.id, bot_message_id)

    if answer_check.is_correct:
        result_message = await message.answer(
            f"✅ Верно!\n\n{listening_result_text(sentence)}",
            reply_markup=listening_result_keyboard(index),
        )
    elif answer_check.is_almost:
        result_message = await message.answer(
            "🟡 Почти верно.\n\n"
            f"Твой ответ:\n{message.text or ''}\n\n"
            f"Правильно:\n{listening_result_text(sentence)}",
            reply_markup=listening_result_keyboard(index),
        )
    else:
        result_message = await message.answer(
            f"❌ Неверно.\n\nПравильный ответ:\n{listening_result_text(sentence)}",
            reply_markup=listening_result_keyboard(index),
        )
    remember_transient_user_message(message.chat.id, result_message.message_id, message.message_id)
