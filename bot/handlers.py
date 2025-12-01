from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from collections import Counter, defaultdict
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from aiogram.filters import Command
from aiogram import F, Router
import asyncio

from bot.keyboards import (
    cause_keyboard,
    language_keyboard,
    main_menu_keyboard,
    mood_keyboard,
    quiz_answer_keyboard,
    stress_keyboard,
    cause_labels,
    stress_labels,
)
from bot.states import AppStates
from database.db import checkins_collection, stress_collection
from database.models import CheckIn, StressTestResult
from utils.language import resolve_language, update_language
from config import get_settings
from services.gemini import generate_gemini
from utils.texts import (
    get_language_label,
    get_list,
    get_quiz,
    get_quiz_button_map,
    get_stress_level_labels,
    get_text,
    language_button_labels,
    get_random_quote,
)

router = Router()


class CheckInStates(StatesGroup):
    mood = State()
    cause = State()


class StressTestStates(StatesGroup):
    question = State()


QUIZ_BUTTON_MAP = get_quiz_button_map()
LANGUAGE_BUTTONS = set(language_button_labels())

MOOD_VALUES = {
    "great": 5,
    "fine": 4,
    "okay": 3,
    "bad": 2,
    "tired": 2,
    "angry": 1,
}


def format_triggers(counter: Counter, language: str) -> str:
    if not counter:
        return get_text("triggers_empty", language)
    labels = cause_labels(language)
    max_count = max(counter.values())
    top = [labels.get(key, str(key)) for key, value in counter.items() if value == max_count]
    return ", ".join(top)


def stress_level(score: int, language: str) -> str:
    labels = get_stress_level_labels(language)
    if score <= 2:
        return labels.get("low")
    if score <= 5:
        return labels.get("medium")
    return labels.get("high")


def quiz_header(quiz: dict) -> str:
    return f"{quiz['badge']} {quiz['title']}"


def quiz_result_text(quiz_key: str, score: int, total: int, language: str) -> str:
    quiz = get_quiz(language, quiz_key)
    level = ""
    advice = ""
    for max_score, label, tip in quiz["ranges"]:
        level = label
        advice = tip
        if score <= max_score:
            break
    return (
        f"{get_text('quiz_completed', language).format(quiz_header=quiz_header(quiz))}\n"
        f"{get_text('score_label', language)} {score}/{total}\n"
        f"{get_text('result_label', language)} {level}\n"
        f"{get_text('advice_label', language)} {advice}"
    )


@router.message(F.text.in_(["✨ Қолдау цитатасы", "✨ Цитата поддержки"]))
async def send_support_quote(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    quote = get_random_quote(language)
    await message.answer(quote, reply_markup=main_menu_keyboard(language))


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await state.clear()
    await state.set_state(AppStates.idle)
    await state.update_data(language=language)
    await message.answer(
        get_text("start_prompt", language),
        reply_markup=main_menu_keyboard(language),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.message(Command("checkin"))
async def cmd_checkin(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await state.clear()
    await state.set_state(CheckInStates.mood)
    await state.update_data(language=language)
    await message.answer(get_text("greeting", language), reply_markup=mood_keyboard(language))


@router.message(Command("language"))
@router.message(F.text.in_(LANGUAGE_BUTTONS))
async def choose_language(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await message.answer(get_text("language_prompt", language), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def apply_language(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = callback.data.split(":", 1)[1]
    language = await update_language(state, callback.from_user.id, language_code)
    await callback.message.answer(
        get_text("language_updated", language).format(language=get_language_label(language)),
        reply_markup=main_menu_keyboard(language),
    )
    await callback.answer()


@router.message(F.text == "🤖 CHAT AI")
async def start_chat(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    current_state = await state.get_state()
    if current_state == AppStates.quiz.state:
        await message.answer(get_text("finish_quiz_first", language))
        return
    await state.clear()
    await state.set_state(AppStates.chat)
    await state.update_data(language=language)
    await message.answer(
        get_text("chat_started", language),
        reply_markup=main_menu_keyboard(language),
    )


@router.message(F.text.in_(QUIZ_BUTTON_MAP))
async def start_quiz(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    quiz_key = QUIZ_BUTTON_MAP.get(message.text)
    if not quiz_key:
        await message.answer(get_text("unknown_quiz", language))
        return
    await state.set_state(AppStates.quiz)
    await state.update_data(quiz_key=quiz_key, index=0, score=0)
    quiz = get_quiz(language, quiz_key)
    await message.answer(
        get_text("quiz_intro", language).format(quiz_header=quiz_header(quiz)),
        reply_markup=main_menu_keyboard(language),
    )
    await message.answer(quiz["questions"][0], reply_markup=quiz_answer_keyboard(language))


@router.callback_query(CheckInStates.mood, F.data.startswith("mood:"))
async def handle_mood(callback: CallbackQuery, state: FSMContext) -> None:
    language = await resolve_language(state, callback.from_user.id)
    mood = callback.data.split(":", 1)[1]
    await state.update_data(mood=mood)
    await state.set_state(CheckInStates.cause)
    await callback.message.answer(get_text("checkin_prompt", language), reply_markup=cause_keyboard(language))
    await callback.answer()


@router.callback_query(CheckInStates.cause, F.data.startswith("cause:"))
async def handle_cause(callback: CallbackQuery, state: FSMContext) -> None:
    language = await resolve_language(state, callback.from_user.id)
    cause = callback.data.split(":", 1)[1]
    data = await state.get_data()
    mood = data.get("mood")
    checkin = CheckIn(user_id=callback.from_user.id, mood=mood, cause=cause)
    await checkins_collection.insert_one(checkin.dict())
    await state.clear()
    await state.set_state(AppStates.idle)
    await state.update_data(language=language)
    await callback.message.answer(get_text("checkin_thanks", language), reply_markup=main_menu_keyboard(language))
    await callback.answer()


@router.callback_query(AppStates.quiz, F.data.startswith("quiz_answer:"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    language = await resolve_language(state, callback.from_user.id)
    data = await state.get_data()
    quiz_key: str = data.get("quiz_key")
    index: int = data.get("index", 0)
    score: int = data.get("score", 0)
    if not quiz_key:
        await callback.message.answer(get_text("quiz_not_found", language))
        await state.clear()
        await callback.answer()
        return
    quiz = get_quiz(language, quiz_key)
    answer_value = callback.data.split(":", 1)[1]
    if answer_value == "yes":
        score += 1
    index += 1
    total = len(quiz["questions"])
    if index >= total:
        result_text = quiz_result_text(quiz_key, score, total, language)
        await callback.message.answer(result_text, reply_markup=main_menu_keyboard(language))
        await state.clear()
        await state.set_state(AppStates.idle)
        await state.update_data(language=language)
        await callback.answer()
        return
    await state.update_data(index=index, score=score, quiz_key=quiz_key)
    await callback.message.answer(quiz["questions"][index], reply_markup=quiz_answer_keyboard(language))
    await callback.answer()


@router.message(AppStates.quiz)
async def quiz_text_block(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await message.answer(get_text("quiz_in_progress", language))


settings = get_settings()


@router.message(AppStates.chat)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает сообщения в режиме CHAT AI, вызывает Gemini с историей
    и обновляет историю.
    """
    if not message.text:
        return

    user_id = message.from_user.id

    await message.bot.send_chat_action(chat_id=user_id, action="typing")

    data = await state.get_data()

    history = data.get("chat_history", [])

    user_prompt = message.text

    ai_response_text = await generate_gemini(
        history=history,
        new_prompt=user_prompt,
        system_prompt=settings.SYSTEM_PROMPT
    )

    history.append({"role": "user", "text": user_prompt})
    history.append({"role": "model", "text": ai_response_text})

    await state.update_data(chat_history=history[-20:])

    await message.answer(ai_response_text, reply_markup=main_menu_keyboard(data.get("language")))


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    since = datetime.utcnow() - timedelta(days=7)
    cursor = checkins_collection.find({"user_id": message.from_user.id, "date": {"$gte": since}})
    entries = await cursor.to_list(length=1000)
    if not entries:
        await message.answer(get_text("stats_empty", language))
        return
    scores = []
    triggers = Counter()
    daily = defaultdict(list)
    for entry in entries:
        score = entry.get("mood_score")
        if score is None:
            mood = entry.get("mood")
            score = MOOD_VALUES.get(mood, 3)
        scores.append(score)
        triggers[entry.get("cause")] += 1
        day = entry.get("date")
        if isinstance(day, datetime):
            day_key = day.date()
        else:
            day_key = datetime.fromisoformat(day).date()
        daily[day_key].append(score)
    average = sum(scores) / len(scores)
    best_day = max(daily.items(), key=lambda item: sum(item[1]) / len(item[1]))
    worst_day = min(daily.items(), key=lambda item: sum(item[1]) / len(item[1]))
    best_avg = sum(best_day[1]) / len(best_day[1])
    worst_avg = sum(worst_day[1]) / len(worst_day[1])
    lines = [
        get_text("stats_title", language),
        f"{get_text('stats_count', language)} {len(entries)}",
        f"{get_text('stats_average', language)} {average:.2f}",
        f"{get_text('stats_triggers', language)} {format_triggers(triggers, language)}",
        f"{get_text('stats_best_day', language)} {best_day[0].isoformat()} ({get_text('stats_average', language).lower()} {best_avg:.2f})",
        f"{get_text('stats_worst_day', language)} {worst_day[0].isoformat()} ({get_text('stats_average', language).lower()} {worst_avg:.2f})",
    ]
    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard(language))


@router.message(Command("mood"))
async def cmd_mood_scale(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer(get_text("mood_usage", language))
        return
    try:
        score = int(message.text.split(maxsplit=1)[1])
    except ValueError:
        await message.answer(get_text("mood_integer", language))
        return
    if not 1 <= score <= 10:
        await message.answer(get_text("mood_range", language))
        return
    checkin = CheckIn(user_id=message.from_user.id, mood="scale", cause="scale", mood_score=score)
    await checkins_collection.insert_one(checkin.dict())
    await message.answer(get_text("mood_saved", language).format(score=score))


@router.message(Command("stress_test"))
async def cmd_stress_test(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await state.set_state(StressTestStates.question)
    await state.update_data(index=0, score=0, details=[])
    await message.answer(get_text("stress_intro", language))
    questions = get_list("stress_questions", language)
    await message.answer(questions[0], reply_markup=stress_keyboard(language))


@router.callback_query(StressTestStates.question, F.data.startswith("stress:"))
async def handle_stress(callback: CallbackQuery, state: FSMContext) -> None:
    language = await resolve_language(state, callback.from_user.id)
    value = callback.data.split(":", 1)[1]
    data = await state.get_data()
    index = data.get("index", 0)
    score = data.get("score", 0)
    details: list[str] = data.get("details", [])
    questions = get_list("stress_questions", language)
    if value == "yes":
        score += 1
    labels = stress_labels(language)
    if index < len(questions):
        details.append(f"{questions[index]} - {labels.get(value, value)}")
    index += 1
    if index >= len(questions):
        level = stress_level(score, language)
        result = StressTestResult(
            user_id=callback.from_user.id,
            score=score,
            level=level,
            details=details,
        )
        await stress_collection.insert_one(result.dict())
        await callback.message.answer(
            f"{get_text('stress_completed', language)}\n"
            f"{get_text('stress_score_label', language)} {score}/{len(questions)}\n"
            f"{get_text('stress_level_label', language)} {level.title()}",
            reply_markup=main_menu_keyboard(language),
        )
        await state.clear()
        await state.set_state(AppStates.idle)
        await state.update_data(language=language)
        await callback.answer()
        return
    await state.update_data(index=index, score=score, details=details)
    await callback.message.answer(questions[index], reply_markup=stress_keyboard(language))
    await callback.answer()


@router.message(Command("panic"))
async def cmd_panic(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await message.answer(get_text("panic_intro", language))
    for step in get_list("panic_breathing_steps", language):
        await asyncio.sleep(1)
        await message.answer(step)
    for step in get_list("panic_grounding_steps", language):
        await asyncio.sleep(1)
        await message.answer(step)


@router.message(Command("breath"))
async def cmd_breath(message: Message, state: FSMContext) -> None:
    language = await resolve_language(state, message.from_user.id)
    await message.answer(get_text("breath_intro", language))
    for step in get_list("breath_steps", language):
        await asyncio.sleep(1)
        await message.answer(step)
