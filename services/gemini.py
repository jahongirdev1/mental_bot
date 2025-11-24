import asyncio
from google.genai import Client
from config import settings


client = Client(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = (
    "Сен қазақ тілінде сөйлейтін мейірімді психологиялық ассистентсің. "
    "Эмоцияны байқап, ықтимал себепті көрсетіп, үш қысқа кеңес бер. "
    "Өзін-өзі жарақаттау туралы мәтін болса, қауіпсіздік туралы ескерту қос."
)


def _generate(prompt: str) -> str:
    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\nПайдаланушы: {prompt}"}
                    ]
                }
            ]
        )
        return response.text or "Кешіріңіз, жауап бере алмадым."

    except Exception as e:
        return f"Қате пайда болды: {e}"


async def generate_gemini(prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _generate(prompt))
