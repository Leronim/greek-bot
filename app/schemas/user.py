from pydantic import BaseModel


class UserSettingsSchema(BaseModel):
    level_mode: str = "A1"
    daily_new_words: int = 5
    typing_direction: str = "mixed"
    show_transcription: bool = True
    show_examples: bool = True
    reminders_enabled: bool = False
