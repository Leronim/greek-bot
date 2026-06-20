from dataclasses import dataclass


@dataclass(frozen=True)
class WordSection:
    kind: str
    value: str
    title: str


SECTIONS: dict[str, WordSection] = {
    "professions": WordSection(kind="topic", value="Профессии", title="Профессии"),
    "verbs": WordSection(kind="topic", value="Глаголы", title="Глаголы"),
    "lesson_1": WordSection(kind="lesson", value="Урок 1", title="Глава 1"),
    "lesson_2": WordSection(kind="lesson", value="Урок 2", title="Глава 2"),
    "lesson_3": WordSection(kind="lesson", value="Урок 3", title="Глава 3"),
    "lesson_4": WordSection(kind="lesson", value="Урок 4", title="Глава 4"),
    "lesson_5": WordSection(kind="lesson", value="Урок 5", title="Глава 5"),
    "lesson_6": WordSection(kind="lesson", value="Урок 6", title="Глава 6"),
    "lesson_7": WordSection(kind="lesson", value="Урок 7", title="Глава 7"),
    "lesson_8": WordSection(kind="lesson", value="Урок 8", title="Глава 8"),
}

_user_sections: dict[int, WordSection] = {}


def get_section(code: str) -> WordSection | None:
    return SECTIONS.get(code)


def set_user_section(user_id: int, section: WordSection) -> None:
    _user_sections[user_id] = section


def get_user_section(user_id: int) -> WordSection | None:
    return _user_sections.get(user_id)


def clear_user_section(user_id: int) -> None:
    _user_sections.pop(user_id, None)
