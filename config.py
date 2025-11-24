from functools import lru_cache
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    BOT_TOKEN: str = "8396786108:AAGUXwTi5DJ0Yp4G7336EmKMpQEsvhDFS5w"
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "mental_bot"
    GEMINI_API_KEY: str = "AIzaSyBpu-VIM1zogV0oTI4kivRuPwdzxq90YjA"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
