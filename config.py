from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str = "your_token_here"
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "mental_bot"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
