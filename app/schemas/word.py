from pydantic import BaseModel


class WordImportSchema(BaseModel):
    id: str
    level: str
    topic: str
    greek: str
    transcription: str | None = None
    ru: str
    part_of_speech: str | None = None
    gender: str | None = None
    example_el: str | None = None
    example_ru: str | None = None
    greek_answers: list[str] = []
    ru_answers: list[str] = []
    is_active: bool = True
