from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards.sections import sections_keyboard
from app.bot.keyboards.typing import typing_mode_keyboard
from app.models import User
from app.services import section_service
from app.services.audio_service import delete_transient_audio, delete_transient_user_messages

router = Router()


@router.callback_query(F.data == "sections:menu")
async def sections_menu(callback: CallbackQuery) -> None:
    await delete_transient_audio(callback.bot, callback.message.chat.id, callback.message.message_id)
    await delete_transient_user_messages(callback.bot, callback.message.chat.id, callback.message.message_id)
    await callback.message.edit_text("📂 Разделы\n\nВыбери, что хочешь писать:", reply_markup=sections_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("sections:set:"))
async def sections_set(callback: CallbackQuery, db_user: User) -> None:
    code = callback.data.rsplit(":", 1)[-1]
    section = section_service.get_section(code)
    if section is None:
        await callback.answer("Раздел не найден", show_alert=True)
        return

    section_service.set_user_section(db_user.id, section)
    await callback.message.edit_text(
        f"📂 Раздел: {section.title}\n\nВыбери направление:",
        reply_markup=typing_mode_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "sections:clear")
async def sections_clear(callback: CallbackQuery, db_user: User) -> None:
    section_service.clear_user_section(db_user.id)
    await callback.message.edit_text(
        "📂 Раздел: все слова\n\nВыбери направление:",
        reply_markup=typing_mode_keyboard(),
    )
    await callback.answer()
