from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models import User
from app.repositories import settings_repo, words_repo
from app.services.progress_service import mark_manual_result

router = Router()


def review_keyboard(word_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать ответ", callback_data=f"review:show:{word_id}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def review_result_keyboard(word_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Знал", callback_data=f"review:knew:{word_id}"),
                InlineKeyboardButton(text="❌ Не знал", callback_data=f"review:miss:{word_id}"),
            ],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def review_continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующее слово", callback_data="review:start")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


@router.message(Command("review"))
async def review_command(message: Message, session: AsyncSession, db_user: User) -> None:
    settings = await settings_repo.get_settings(session, db_user.id)
    word = await words_repo.get_due_word(session, db_user.id, settings.level_mode)
    if word is None:
        await message.answer("Сейчас нет слов к повторению.", reply_markup=main_menu_keyboard())
        return
    transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
    await message.answer(f"🔁 Повторение\n\n🇬🇷 {word.greek}{transcription}\n\nВспомни перевод.", reply_markup=review_keyboard(word.id))


@router.callback_query(F.data == "review:start")
async def review_start(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    settings = await settings_repo.get_settings(session, db_user.id)
    word = await words_repo.get_due_word(session, db_user.id, settings.level_mode)
    if word is None:
        await callback.message.edit_text("Сейчас нет слов к повторению.", reply_markup=main_menu_keyboard())
    else:
        transcription = f"\n🔊 {word.transcription}" if word.transcription else ""
        await callback.message.edit_text(
            f"🔁 Повторение\n\n🇬🇷 {word.greek}{transcription}\n\nВспомни перевод.",
            reply_markup=review_keyboard(word.id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("review:show:"))
async def review_show(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    word = await words_repo.get_word(session, word_id)
    if word is None:
        await callback.message.edit_text("Слово не найдено.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(f"🇬🇷 {word.greek}\n🇷🇺 {word.ru}\n\nТы знал?", reply_markup=review_result_keyboard(word.id))
    await callback.answer()


@router.callback_query(F.data.startswith("review:knew:"))
async def review_knew(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    await mark_manual_result(session, db_user.id, word_id, knew=True)
    await callback.message.edit_text("✅ Принято.", reply_markup=review_continue_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("review:miss:"))
async def review_miss(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    word_id = int(callback.data.rsplit(":", 1)[-1])
    await mark_manual_result(session, db_user.id, word_id, knew=False)
    await callback.message.edit_text("❌ Слово вернётся на повторение позже.", reply_markup=review_continue_keyboard())
    await callback.answer()
