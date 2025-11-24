from functools import lru_cache
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    BOT_TOKEN: str = "7089495505:AAF21wmxnoBLJAPFa9ERGqLHKq-EpUoTxpk"
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "mental_bot"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
