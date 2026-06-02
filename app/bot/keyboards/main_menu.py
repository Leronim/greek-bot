from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Урок", callback_data="lesson:start"),
                InlineKeyboardButton(text="🔁 Повторение", callback_data="review:start"),
            ],
            [
                InlineKeyboardButton(text="✍️ Написать ответ", callback_data="typing:menu"),
                InlineKeyboardButton(text="🧠 Тест", callback_data="quiz:start"),
            ],
            [InlineKeyboardButton(text="💬 Предложения", callback_data="sentences:start")],
            [InlineKeyboardButton(text="📊 Прогресс", callback_data="stats:show")],
        ]
    )
