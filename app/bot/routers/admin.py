from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.services.import_service import import_words_from_json

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_set


@router.message(Command("admin"))
async def admin(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return
    await message.answer("Админка:\n/admin_import - отправь JSON-файл со словами после этой команды.")


@router.message(Command("admin_import"))
async def admin_import_hint(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return
    await message.answer("Пришли JSON-файл со словами. Формат как в data/words_a1.json.")


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
