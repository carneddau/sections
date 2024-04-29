from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "ERROR"
    model_config = SettingsConfigDict(env_file=".env")


@cache
def get_settings():
    return Settings()
