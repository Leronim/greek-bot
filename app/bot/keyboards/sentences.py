from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sentence_card_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать перевод", callback_data=f"sentences:show:{index}")],
            [InlineKeyboardButton(text="Следующая фраза", callback_data=f"sentences:next:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def sentence_result_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Следующая фраза", callback_data=f"sentences:next:{index}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
