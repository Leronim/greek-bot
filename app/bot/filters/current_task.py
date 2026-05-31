from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import progress_repo


class CurrentTaskFilter(BaseFilter):
    def __init__(self, task_type: str) -> None:
        self.task_type = task_type

    async def __call__(self, message: Message, session: AsyncSession, db_user: User) -> bool:
        task = await progress_repo.get_current_task(session, db_user.id)
        return task is not None and task.task_type == self.task_type
