from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def quiz_keyboard(word_id: int, correct: str, options: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for option in options:
        marker = "1" if option == correct else "0"
        rows.append([InlineKeyboardButton(text=option, callback_data=f"quiz:answer:{word_id}:{marker}")])
    rows.append([InlineKeyboardButton(text="В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def after_quiz_keyboard(word_id: int | None = None) -> InlineKeyboardMarkup:
    audio_row = []
    if word_id is not None:
        audio_row = [[InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:quiz:word:{word_id}")]]
    return InlineKeyboardMarkup(
        inline_keyboard=audio_row
        + [
            [InlineKeyboardButton(text="Следующий тест", callback_data="quiz:start")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
