from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def listening_task_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Повторить", callback_data=f"audio:sentence:{index}")],
            [InlineKeyboardButton(text="Показать ответ", callback_data=f"listening:show:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def listening_result_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:sentence:{index}")],
            [InlineKeyboardButton(text="Следующая фраза", callback_data=f"listening:next:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
