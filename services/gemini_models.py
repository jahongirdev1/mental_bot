"""
Gemini model registry — барлық модель атаулары, қолжетімді модельдерді шығару.
google-genai (1.52.0) SDK үшін.
"""

from google.genai import Client
from config import settings

client = Client(api_key=settings.GEMINI_API_KEY)

# --- Барлық модельдер ---
GEMINI_MODELS = {
    "flash_v1_5":       "gemini-1.5-flash-latest",
    "pro_v1_5":         "gemini-1.5-pro-latest",
    "flash_v2_0":       "gemini-2.0-flash",
    "flash_v2_0_think": "gemini-2.0-flash-thinking",
    "pro_v2_0":         "gemini-2.0-pro",
}

# FREE API-key үшін default:
DEFAULT_MODEL = GEMINI_MODELS["flash_v1_5"]


def list_available_models() -> list[str]:
    """
    API-key қолдайтын модельдер тізімін қайтарады.
    """
    try:
        models = client.models.list()
        return [m.name for m in models]
    except Exception as e:
        return [f"Қате: {e}"]


def get_model(name: str) -> str:
    """
    Қысқа alias → нақты модель атына ауыстыру.
    Егер жоқ болса default қайтарады.
    """
    return GEMINI_MODELS.get(name, DEFAULT_MODEL)
