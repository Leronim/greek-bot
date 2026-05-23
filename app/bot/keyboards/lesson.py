from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def lesson_card_keyboard(word_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:word:{word_id}")],
            [InlineKeyboardButton(text="Показать перевод", callback_data=f"lesson:show:{word_id}")],
            [
                InlineKeyboardButton(text="Уже знаю", callback_data=f"lesson:knew:{word_id}"),
                InlineKeyboardButton(text="⭐ В сложные", callback_data=f"lesson:hard:{word_id}"),
            ],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def lesson_result_keyboard(word_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:word:{word_id}")],
            [
                InlineKeyboardButton(text="✅ Запомнил", callback_data=f"lesson:knew:{word_id}"),
                InlineKeyboardButton(text="❌ Нужно повторить", callback_data=f"lesson:again:{word_id}"),
            ],
            [InlineKeyboardButton(text="Следующее", callback_data="lesson:start")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def lesson_continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующее слово", callback_data="lesson:start")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
