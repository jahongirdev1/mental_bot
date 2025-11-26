from aiogram.fsm.context import FSMContext

from services.user_settings import get_user_language, set_user_language
from utils.texts import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


async def resolve_language(state: FSMContext, user_id: int) -> str:
    data = await state.get_data()
    language = data.get("language") if data else None
    if language in SUPPORTED_LANGUAGES:
        return language
    language = await get_user_language(user_id)
    await state.update_data(language=language)
    return language


async def update_language(state: FSMContext, user_id: int, language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    await set_user_language(user_id, language)
    await state.update_data(language=language)
    return language
