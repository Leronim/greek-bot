from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.models import User
from app.bot.routers.sentences import clear_sentence_task
from app.services.audio_service import delete_transient_audio, delete_transient_user_messages

router = Router()


@router.message(Command("menu", "help"))
async def menu_command(message: Message, db_user: User) -> None:
    clear_sentence_task(db_user.id)
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def menu_callback(callback: CallbackQuery, db_user: User) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    clear_sentence_task(db_user.id)
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
