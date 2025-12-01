from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message
from bot.states import AppStates
from aiogram import F, Router
import asyncio

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from services.gemini import generate_gemini
from utils.language import resolve_language
from utils.texts import get_text
from config import get_settings  # Для SYSTEM_PROMPT
from bot.keyboards import main_menu_keyboard  # Для клавиатуры после ответа

# ---------------------------

router = Router()
settings = get_settings()


# Вспомогательная функция, которая теперь использует пустой список истории
async def _ask_gemini(user_text: str, language: str) -> str:
    # 1. Формируем prompt для одноразового запроса
    prompt = get_text("ai_chat_prompt", language).format(user_text=user_text)
    prompt = f"{prompt}\n{get_text('fallback_prompt', language)}"

    # 2. Вызываем новую функцию generate_gemini с ПУСТОЙ историей (stateless)
    return await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )


async def _ensure_chat_mode(message: Message, state: FSMContext, language: str) -> bool:
    current_state = await state.get_state()
    if current_state == AppStates.quiz.state:
        await message.answer(get_text("finish_quiz_first", language))
        return False
    if current_state and current_state != AppStates.chat.state:
        await message.answer(get_text("complete_other_step", language))
        return False
    if current_state != AppStates.chat.state:
        # Убираем "start_chat_first" и переводим в чат-режим
        await state.set_state(AppStates.chat)
        await message.answer(get_text("chat_started", language), reply_markup=main_menu_keyboard(language))
        return True  # Разрешаем продолжить, т.к. только что переключились
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

    # AI в режиме одноразового ответа
    reply = await _ask_gemini(user_text, language)
    await message.answer(reply)


# Все остальные команды обновляются по тому же принципу:
# вызываем generate_gemini с пустой историей [] и settings.SYSTEM_PROMPT

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

    # Вызов с пустой историей
    reply = await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )
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

    # Вызов с пустой историей
    reply = await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )
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

    # Вызов с пустой историей
    reply = await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )
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

    # Вызов с пустой историей
    reply = await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )
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

    # Вызов с пустой историей
    reply = await generate_gemini(
        history=[],
        new_prompt=prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )
    await message.answer(reply)


# --- ОСНОВНОЙ ОБРАБОТЧИК ДЛЯ ЧАТА AI С ПАМЯТЬЮ (КОНТЕКСТОМ) ---
@router.message(AppStates.chat, F.text)
async def fallback_ai(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)

    # Отправляем "печатает..."
    await message.bot.send_chat_action(chat_id=message.from_user.id, action="typing")

    data = await state.get_data()
    # history - это список объектов: [{"role": "user", "text": "..."}, {"role": "model", "text": "..."}]
    history = data.get("chat_history", [])
    user_prompt = message.text

    # 1. Формируем prompt (в данном случае, просто текст пользователя)
    # Используем `ai_chat_prompt` и `fallback_prompt` для общей беседы, как в вашей старой логике
    final_prompt = (
        f"{get_text('ai_chat_prompt', language).format(user_text=message.text)}\n"
        f"{get_text('fallback_prompt', language)}"
    )

    # 2. Вызываем Gemini, передавая ИСТОРИЮ
    ai_response_text = await generate_gemini(
        history=history,
        new_prompt=final_prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )

    # 3. Обновляем историю для следующего сообщения
    history.append({"role": "user", "text": user_prompt})  # Сохраняем чистый текст пользователя
    history.append({"role": "model", "text": ai_response_text})

    # Ограничиваем историю до последних 20 сообщений
    await state.update_data(chat_history=history[-20:])

    # 4. Отправляем ответ пользователю
    await message.answer(ai_response_text, reply_markup=main_menu_keyboard(language))