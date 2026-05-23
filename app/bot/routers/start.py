from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Γεια σου!\n\nЯ помогу учить греческие слова A1 через письменные ответы и повторение.",
        reply_markup=main_menu_keyboard(),
    )
