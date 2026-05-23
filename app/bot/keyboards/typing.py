from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def typing_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 → 🇬🇷", callback_data="typing:start:ru_to_el")],
            [InlineKeyboardButton(text="🇬🇷 → 🇷🇺", callback_data="typing:start:el_to_ru")],
            [InlineKeyboardButton(text="🔀 Смешанный", callback_data="typing:start:mixed")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )


def after_typing_keyboard(word_id: int | None = None) -> InlineKeyboardMarkup:
    example_callback = f"typing:example:{word_id}" if word_id is not None else "typing:example"
    audio_row = []
    if word_id is not None:
        audio_row = [[InlineKeyboardButton(text="🔊 Озвучить", callback_data=f"audio:typing:word:{word_id}")]]
    return InlineKeyboardMarkup(
        inline_keyboard=audio_row
        + [
            [InlineKeyboardButton(text="Следующее", callback_data="typing:next")],
            [InlineKeyboardButton(text="Показать пример", callback_data=example_callback)],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
