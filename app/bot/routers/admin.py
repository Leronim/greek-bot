from pathlib import Path
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import settings
from app.models import User
from app.services.import_service import import_words_from_json

router = Router()
_pending_broadcasts: dict[int, str] = {}


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_set


@router.message(Command("admin"))
async def admin(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return
    await message.answer(
        "Админка:\n"
        "/admin_import - отправь JSON-файл со словами после этой команды.\n"
        "/admin_broadcast текст - отправить сообщение всем пользователям."
    )


@router.message(Command("admin_import"))
async def admin_import_hint(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return
    await message.answer("Пришли JSON-файл со словами. Формат как в data/words_a1.json.")


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отправить", callback_data="admin_broadcast:confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="admin_broadcast:cancel"),
            ]
        ]
    )


@router.message(Command("admin_broadcast"))
async def admin_broadcast(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return

    text = (message.text or "").replace("/admin_broadcast", "", 1).strip()
    if not text:
        await message.answer("Напиши текст после команды:\n/admin_broadcast Новость для пользователей")
        return

    _pending_broadcasts[message.from_user.id] = text
    await message.answer(
        f"Предпросмотр рассылки:\n\n{text}\n\nОтправить всем пользователям?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "admin_broadcast:cancel")
async def admin_broadcast_cancel(callback: CallbackQuery) -> None:
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Команда доступна только администратору.", show_alert=True)
        return

    _pending_broadcasts.pop(callback.from_user.id, None)
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast:confirm")
async def admin_broadcast_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Команда доступна только администратору.", show_alert=True)
        return

    text = _pending_broadcasts.pop(callback.from_user.id, None)
    if not text:
        await callback.message.edit_text("Нет подготовленной рассылки.")
        await callback.answer()
        return

    result = await session.execute(select(User.telegram_id).order_by(User.id))
    telegram_ids = list(result.scalars())

    sent = 0
    failed = 0
    await callback.message.edit_text(f"Рассылка запущена. Пользователей: {len(telegram_ids)}")

    for telegram_id in telegram_ids:
        try:
            await callback.bot.send_message(telegram_id, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(f"Рассылка завершена.\nОтправлено: {sent}\nОшибок: {failed}")
    await callback.answer()


@router.message(F.document)
async def admin_import_file(message: Message, session: AsyncSession) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        return
    if message.document is None or not message.document.file_name.endswith(".json"):
        await message.answer("Нужен JSON-файл.")
        return

    temp_dir = Path("data/imports")
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / message.document.file_name
    await message.bot.download(message.document, destination=path)
    imported = await import_words_from_json(session, path)
    await message.answer(f"Импорт завершён. Новых слов: {imported}.")
