from functools import cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    log_level: str = "ERROR"

    class Config:
        env_file = ".env"


@cache
def get_settings():
    return Settings()
