from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.services.audio_service import delete_transient_audio

router = Router()


@router.message(Command("menu", "help"))
async def menu_command(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def menu_callback(callback: CallbackQuery) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
