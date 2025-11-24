"""AI жауаптарын Gemini арқылы беретін хэндлерлер."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.gemini import SYSTEM_PROMPT, generate_gemini
from bot.states import AppStates


router = Router()


async def _ask_gemini(user_text: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nПайдаланушының мәтіні: {user_text}\n\nКөмекші:" \
        " эмоция → себеп → 3 кеңес → қолдау форматын сақтасын."
    return await generate_gemini(prompt)


async def _ensure_chat_mode(message: Message, state: FSMContext) -> bool:
    current_state = await state.get_state()
    if current_state == AppStates.quiz.state:
        await message.answer("Алдымен тестті аяқтаңыз, содан кейін CHAT AI батырмасын басыңыз.")
        return False
    if current_state and current_state != AppStates.chat.state:
        await message.answer(
            "Қазір басқа қадам жүріп жатыр. Басты мәзірден CHAT AI батырмасын баспас бұрын оны аяқтаңыз."
        )
        return False
    if current_state != AppStates.chat.state:
        await message.answer("AI-пен сөйлесу үшін басты мәзірдегі CHAT AI батырмасын басыңыз.")
        return False
    return True


@router.message(Command("ai"))
async def cmd_ai(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("/ai кейін мәселе немесе ойыңызды жазыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    reply = await _ask_gemini(user_text)
    await message.answer(reply)


@router.message(Command("emo"))
async def cmd_emotion(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("Эмоцияны анықтау үшін /emo кейін мәтін жазыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = (
        f"{SYSTEM_PROMPT}\n\nЭмоцияны қысқа ата, ықтимал себепті көрсет және 3 қолдау кеңесін жаз."
        f" Мәтін: {user_text}"
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)


@router.message(Command("reframe"))
async def cmd_reframe(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("Теріс ойды қайта қарау үшін /reframe кейін ойды жазыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = (
        f"{SYSTEM_PROMPT}\n\nТеріс ойды CBT тәсілімен қайта құрыңыз."
        f" Эмоция → себеп → 3 жаңа ой → қолдау форматын сақта. Ой: {user_text}"
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)


@router.message(Command("decision"))
async def cmd_decision(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("Мәселені жазу үшін /decision кейін мәтін қосыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = (
        f"{SYSTEM_PROMPT}\n\nПроблеманы шешу үшін 3 нақты қадам ұсын."
        f" Әр қадам қысқа әрекет болсын. Мәселе: {user_text}"
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)


@router.message(Command("stress_ai"))
async def cmd_stress_ai(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("Стресс туғызатын жағдайды /stress_ai кейін жазыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = (
        f"{SYSTEM_PROMPT}\n\nМәтінді оқып, стресс деңгейін (төмен/орташа/жоғары) белгіле."
        f" Себебін қысқа түсіндіріп, 3 нақты кеңес бер. Мәтін: {user_text}"
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)


@router.message(Command("mental_ai"))
async def cmd_mental_ai(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("/mental_ai кейін қызықтыратын психология тақырыбын немесе сұрағыңызды жазыңыз.")
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = (
        f"{SYSTEM_PROMPT}\n\nПайдаланушымен психологиялық қолдау аясында еркін сөйлес."
        f" Тақырып: {user_text}. Ашық сұрақ қойып, жылы әрі қысқа жауап бер."
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)


@router.message(AppStates.chat, F.text)
async def fallback_ai(message: Message, state: FSMContext) -> None:
    if not await _ensure_chat_mode(message, state):
        return
    prompt = (
        f"{SYSTEM_PROMPT}\n\nПайдаланушының мәтіні: {message.text}\n"
        "Қысқа әрі нақты жауап бер, эмоция мен қолдауды ұмытпа."
    )
    reply = await generate_gemini(prompt)
    await message.answer(reply)

