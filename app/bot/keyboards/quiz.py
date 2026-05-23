from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def quiz_keyboard(word_id: int, correct: str, options: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for option in options:
        marker = "1" if option == correct else "0"
        rows.append([InlineKeyboardButton(text=option, callback_data=f"quiz:answer:{word_id}:{marker}")])
    rows.append([InlineKeyboardButton(text="В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def after_quiz_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующий тест", callback_data="quiz:start")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
