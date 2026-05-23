from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="settings:level:A1"),
            ],
            [
                InlineKeyboardButton(text="RU→EL", callback_data="settings:direction:ru_to_el"),
                InlineKeyboardButton(text="EL→RU", callback_data="settings:direction:el_to_ru"),
                InlineKeyboardButton(text="Mix", callback_data="settings:direction:mixed"),
            ],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
