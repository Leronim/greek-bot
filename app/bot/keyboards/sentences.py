from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sentence_task_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать ответ", callback_data=f"sentences:show:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def sentence_result_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:sentence:{index}")],
            [InlineKeyboardButton(text="Следующая фраза", callback_data=f"sentences:next:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
