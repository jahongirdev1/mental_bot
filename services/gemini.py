from google.genai import Client
import asyncio
from typing import List, Dict

client = Client(api_key="AIzaSyAwcYSoaxEUQEFcVR6dPsBedo59aaUTMXA")

MODEL = "gemini-2.0-flash"


def _format_history(history: List[Dict[str, str]]) -> str:
    """Преобразует историю сообщений в понятный текст для модели."""
    formatted_lines = []
    for message in history:
        role = message.get("role")
        text = message.get("text", "")
        if role == "user":
            formatted_lines.append(f"Пайдаланушы: {text}")
        elif role == "model":
            formatted_lines.append(f"Ассистент: {text}")
    return "\n".join(formatted_lines)


def _generate(history: List[Dict[str, str]], new_prompt: str, system_prompt: str) -> str:
    try:
        history_block = _format_history(history)
        prompt_text = "\n\n".join(filter(None, [system_prompt, history_block, f"Пайдаланушы: {new_prompt}"]))

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_text}
                    ]
                }
            ]
        )
        return response.text or "Кешіріңіз, жауап бере алмадым."

    except Exception as e:
        return f"Қате пайда болды: {e}"


async def generate_gemini(history: List[Dict[str, str]], new_prompt: str, system_prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _generate(history, new_prompt, system_prompt))
