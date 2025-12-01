from google.genai import Client
import asyncio

client = Client(api_key="AIzaSyAwcYSoaxEUQEFcVR6dPsBedo59aaUTMXA")

MODEL = "gemini-2.0-flash"


def _generate(prompt: str, system_prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_prompt}\n\nПайдаланушы: {prompt}"}
                    ]
                }
            ]
        )
        return response.text or "Кешіріңіз, жауап бере алмадым."

    except Exception as e:
        return f"Қате пайда болды: {e}"


async def generate_gemini(prompt: str, system_prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _generate(prompt, system_prompt))
