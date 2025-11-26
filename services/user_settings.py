from database.db import database
from utils.texts import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

user_settings_collection = database["user_settings"]


async def get_user_language(user_id: int) -> str:
    record = await user_settings_collection.find_one({"user_id": user_id})
    language = record.get("language") if record else None
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


async def set_user_language(user_id: int, language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    await user_settings_collection.update_one(
        {"user_id": user_id}, {"$set": {"language": language}}, upsert=True
    )
