"""Gemini модельімен жұмыс істейтін қарапайым көмекші."""

import asyncio

import google.generativeai as genai

from config import settings


SYSTEM_PROMPT = (
    "Сен қазақ тілінде сөйлейтін мейірімді психологиялық ассистентсің. "
    "Әр жауапта эмоцияны байқап, ықтимал себепті көрсетіп, үш қысқа кеңес бер. "
    "Қауіпті немесе өзін-өзі жарақаттау туралы мәтін болса, қауіпсіздік туралы ескертуді қос."
)


genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def _generate(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text.strip() if response and response.text else "Кешіріңіз, жауап бере алмадым."


async def generate_gemini(prompt: str) -> str:
    """Синхронды Gemini клиентін асинхронды түрде орау."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _generate(prompt))

