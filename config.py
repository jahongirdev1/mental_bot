from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import Field


class Settings(BaseSettings):
    BOT_TOKEN: str = Field("", env="BOT_TOKEN")
    MONGO_URL: str = Field("mongodb://localhost:27017", env="MONGO_URL")
    DB_NAME: str = Field("mental_bot", env="DB_NAME")
    GEMINI_API_KEY: str = Field("", env="GEMINI_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
