from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sections_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Профессии", callback_data="sections:set:professions"),
                InlineKeyboardButton(text="Глаголы", callback_data="sections:set:verbs"),
            ],
            [
                InlineKeyboardButton(text="Глава 1", callback_data="sections:set:lesson_1"),
                InlineKeyboardButton(text="Глава 2", callback_data="sections:set:lesson_2"),
            ],
            [
                InlineKeyboardButton(text="Глава 3", callback_data="sections:set:lesson_3"),
                InlineKeyboardButton(text="Глава 4", callback_data="sections:set:lesson_4"),
            ],
            [
                InlineKeyboardButton(text="Глава 5", callback_data="sections:set:lesson_5"),
                InlineKeyboardButton(text="Глава 6", callback_data="sections:set:lesson_6"),
            ],
            [
                InlineKeyboardButton(text="Глава 7", callback_data="sections:set:lesson_7"),
                InlineKeyboardButton(text="Глава 8", callback_data="sections:set:lesson_8"),
            ],
            [InlineKeyboardButton(text="Все слова", callback_data="sections:clear")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:main")],
        ]
    )
