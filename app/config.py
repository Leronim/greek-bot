from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./greek_bot.db",
        alias="DATABASE_URL",
    )
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    default_timezone: str = Field(default="Asia/Nicosia", alias="DEFAULT_TIMEZONE")
    admin_web_password: str = Field(default="change_me", alias="ADMIN_WEB_PASSWORD")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def admin_id_set(self) -> set[int]:
        values = [item.strip() for item in self.admin_ids.split(",") if item.strip()]
        return {int(item) for item in values}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
