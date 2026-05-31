from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.routers import sentences, typing
from app.models import User
from app.repositories import progress_repo

router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_answer(message: Message, session: AsyncSession, db_user: User) -> None:
    if sentences.has_sentence_task(db_user.id):
        await sentences.handle_sentence_answer(message, session, db_user)
        return

    task = await progress_repo.get_current_task(session, db_user.id)
    if task is not None and task.task_type == "typing":
        await typing.handle_text_answer(message, session, db_user)
        return

    await message.answer("Выбери режим в меню, и я дам задание.", reply_markup=main_menu_keyboard())
