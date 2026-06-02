from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def after_mistake_keyboard(word_id: int | None = None) -> InlineKeyboardMarkup:
    audio_row = []
    if word_id is not None:
        audio_row = [[InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:typing:word:{word_id}")]]
    return InlineKeyboardMarkup(
        inline_keyboard=audio_row
        + [
            [InlineKeyboardButton(text="Следующая ошибка", callback_data="mistakes:next")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
