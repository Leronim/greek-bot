from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("menu", "help"))
async def menu_command(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
