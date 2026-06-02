import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from app.bot.middlewares.db import DbSessionMiddleware
from app.bot.middlewares.user import UserMiddleware
from app.bot.routers import admin, audio, lesson, listening, menu, mistakes, quiz, review, sentences, start, stats, text_answers, typing
from app.config import settings
from app.database import async_session_factory, create_db_schema
from app.services.import_service import import_words_if_empty


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env.")

    await create_db_schema()
    async with async_session_factory() as session:
        await import_words_if_empty(
            session,
            [
                Path("data/words_a1.json"),
            ],
        )
        await session.commit()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(async_session_factory))
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(audio.router)
    dp.include_router(lesson.router)
    dp.include_router(review.router)
    dp.include_router(typing.router)
    dp.include_router(quiz.router)
    dp.include_router(sentences.router)
    dp.include_router(listening.router)
    dp.include_router(mistakes.router)
    dp.include_router(text_answers.router)
    dp.include_router(stats.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
