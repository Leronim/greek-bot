from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models import User
from app.services.stats_service import build_stats_text

router = Router()


@router.message(Command("stats"))
async def stats_command(message: Message, session: AsyncSession, db_user: User) -> None:
    await message.answer(await build_stats_text(session, db_user.id), reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "stats:show")
async def stats_show(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await callback.message.edit_text(await build_stats_text(session, db_user.id), reply_markup=main_menu_keyboard())
    await callback.answer()
