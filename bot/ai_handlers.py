from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message
from bot.states import AppStates
from aiogram import F, Router

from services.gemini import generate_gemini
from utils.language import resolve_language
from utils.texts import get_system_prompt, get_text

router = Router()


async def _ask_gemini(user_text: str, language: str) -> str:
    prompt = get_text("ai_chat_prompt", language).format(user_text=user_text)
    prompt = f"{prompt}\n{get_text('fallback_prompt', language)}"
    return await generate_gemini(prompt, get_system_prompt(language))


async def _ensure_chat_mode(message: Message, state: FSMContext, language: str) -> bool:
    current_state = await state.get_state()
    if current_state == AppStates.quiz.state:
        await message.answer(get_text("finish_quiz_first", language))
        return False
    if current_state and current_state != AppStates.chat.state:
        await message.answer(get_text("complete_other_step", language))
        return False
    if current_state != AppStates.chat.state:
        await message.answer(get_text("start_chat_first", language))
        return False
    return True


@router.message(Command("ai"))
async def cmd_ai(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("ai_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    reply = await _ask_gemini(user_text, language)
    await message.answer(reply)


@router.message(Command("emo"))
async def cmd_emotion(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("emotion_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = get_text("emotion_prompt", language).format(user_text=user_text)
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)


@router.message(Command("reframe"))
async def cmd_reframe(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("reframe_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = get_text("reframe_prompt", language).format(user_text=user_text)
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)


@router.message(Command("decision"))
async def cmd_decision(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("decision_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = get_text("decision_prompt", language).format(user_text=user_text)
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)


@router.message(Command("stress_ai"))
async def cmd_stress_ai(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("stress_ai_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = get_text("stress_ai_prompt", language).format(user_text=user_text)
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)


@router.message(Command("mental_ai"))
async def cmd_mental_ai(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("mental_ai_usage", language))
        return
    user_text = message.text.split(maxsplit=1)[1]
    prompt = get_text("mental_ai_prompt", language).format(user_text=user_text)
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)


@router.message(AppStates.chat, F.text)
async def fallback_ai(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not await _ensure_chat_mode(message, state, language):
        return
    prompt = (
        f"{get_text('ai_chat_prompt', language).format(user_text=message.text)}\n"
        f"{get_text('fallback_prompt', language)}"
    )
    reply = await generate_gemini(prompt, get_system_prompt(language))
    await message.answer(reply)
