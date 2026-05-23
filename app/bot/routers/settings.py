from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.settings import settings_keyboard
from app.models import User
from app.repositories.settings_repo import get_settings

router = Router()


def settings_text(settings) -> str:
    return (
        "⚙️ Настройки\n\n"
        f"Уровень: {settings.level_mode}\n"
        f"Режим ответа: {settings.typing_direction}\n"
        f"Транскрипция: {'да' if settings.show_transcription else 'нет'}\n"
        f"Примеры: {'да' if settings.show_examples else 'нет'}"
    )


@router.message(Command("settings"))
async def settings_command(message: Message, session: AsyncSession, db_user: User) -> None:
    user_settings = await get_settings(session, db_user.id)
    await message.answer(settings_text(user_settings), reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings:show")
async def settings_show(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    user_settings = await get_settings(session, db_user.id)
    await callback.message.edit_text(settings_text(user_settings), reply_markup=settings_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("settings:level:"))
async def settings_level(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    user_settings = await get_settings(session, db_user.id)
    user_settings.level_mode = "A1"
    await callback.message.edit_text(settings_text(user_settings), reply_markup=settings_keyboard())
    await callback.answer("Уровень обновлён")


@router.callback_query(F.data.startswith("settings:direction:"))
async def settings_direction(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    user_settings = await get_settings(session, db_user.id)
    user_settings.typing_direction = value
    await callback.message.edit_text(settings_text(user_settings), reply_markup=settings_keyboard())
    await callback.answer("Режим обновлён")
