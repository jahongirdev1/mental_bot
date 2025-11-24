import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    CAUSE_LABELS,
    back_to_menu_keyboard,
    cause_keyboard,
    mood_keyboard,
    stress_keyboard,
    STRESS_LABELS,
)
from database.db import checkins_collection, stress_collection
from database.models import CheckIn, StressTestResult
from utils.texts import (
    BREATH_INTRO,
    BREATH_STEPS,
    CHECKIN_PROMPT,
    CHECKIN_THANKS,
    GREETING_TEXT,
    PANIC_BREATHING_STEPS,
    PANIC_GROUNDING_STEPS,
    PANIC_INTRO,
    STATS_EMPTY,
    STATS_TITLE,
    STRESS_COMPLETED,
    STRESS_INTRO,
    STRESS_QUESTIONS,
)

router = Router()


class CheckInStates(StatesGroup):
    mood = State()
    cause = State()


class StressTestStates(StatesGroup):
    question = State()


MOOD_VALUES = {
    "great": 5,
    "fine": 4,
    "okay": 3,
    "bad": 2,
    "tired": 2,
    "angry": 1,
}


def format_triggers(counter: Counter) -> str:
    if not counter:
        return "Триггерлер тіркелмеген."
    max_count = max(counter.values())
    top = [CAUSE_LABELS.get(key, str(key)) for key, value in counter.items() if value == max_count]
    return ", ".join(top)


def stress_level(score: int) -> str:
    if score <= 2:
        return "төмен стресс"
    if score <= 5:
        return "орташа стресс"
    return "жоғары стресс"


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CheckInStates.mood)
    await message.answer(GREETING_TEXT, reply_markup=mood_keyboard())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CheckInStates.mood)
    await callback.message.answer(GREETING_TEXT, reply_markup=mood_keyboard())
    await callback.answer()


@router.callback_query(CheckInStates.mood, F.data.startswith("mood:"))
async def handle_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", 1)[1]
    await state.update_data(mood=mood)
    await state.set_state(CheckInStates.cause)
    await callback.message.answer(CHECKIN_PROMPT, reply_markup=cause_keyboard())
    await callback.answer()


@router.callback_query(CheckInStates.cause, F.data.startswith("cause:"))
async def handle_cause(callback: CallbackQuery, state: FSMContext) -> None:
    cause = callback.data.split(":", 1)[1]
    data = await state.get_data()
    mood = data.get("mood")
    checkin = CheckIn(user_id=callback.from_user.id, mood=mood, cause=cause)
    await checkins_collection.insert_one(checkin.dict())
    await state.clear()
    await callback.message.answer(CHECKIN_THANKS, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    since = datetime.utcnow() - timedelta(days=7)
    cursor = checkins_collection.find({"user_id": message.from_user.id, "date": {"$gte": since}})
    entries = await cursor.to_list(length=1000)
    if not entries:
        await message.answer(STATS_EMPTY)
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
        STATS_TITLE,
        f"Жазбалар саны: {len(entries)}",
        f"Орташа көңіл-күй ұпайы: {average:.2f}",
        f"Ең жиі себептер: {format_triggers(triggers)}",
        f"Ең жеңіл күн: {best_day[0].isoformat()} (орташа {best_avg:.2f})",
        f"Қиын күн: {worst_day[0].isoformat()} (орташа {worst_avg:.2f})",
    ]
    await message.answer("\n".join(lines), reply_markup=back_to_menu_keyboard())


@router.message(Command("mood"))
async def cmd_mood_scale(message: Message) -> None:
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.answer("/mood кейін 1-10 аралығындағы ұпайды жазыңыз (мысалы, /mood 7).")
        return
    try:
        score = int(message.text.split(maxsplit=1)[1])
    except ValueError:
        await message.answer("Тек бүтін сан енгізіңіз: 1-ден 10-ға дейін.")
        return
    if not 1 <= score <= 10:
        await message.answer("Ұпай 1-10 аралығында болуы тиіс.")
        return
    checkin = CheckIn(user_id=message.from_user.id, mood="scale", cause="scale", mood_score=score)
    await checkins_collection.insert_one(checkin.dict())
    await message.answer(f"Көңіл-күй ұпайы {score} ретінде сақталды. Рахмет!")


@router.message(Command("stress_test"))
async def cmd_stress_test(message: Message, state: FSMContext) -> None:
    await state.set_state(StressTestStates.question)
    await state.update_data(index=0, score=0, details=[])
    await message.answer(STRESS_INTRO)
    await message.answer(STRESS_QUESTIONS[0], reply_markup=stress_keyboard())


@router.callback_query(StressTestStates.question, F.data.startswith("stress:"))
async def handle_stress(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    data = await state.get_data()
    index = data.get("index", 0)
    score = data.get("score", 0)
    details: list[str] = data.get("details", [])
    if value == "yes":
        score += 1
    details.append(f"{STRESS_QUESTIONS[index]} - {STRESS_LABELS.get(value, value)}")
    index += 1
    if index >= len(STRESS_QUESTIONS):
        level = stress_level(score)
        result = StressTestResult(
            user_id=callback.from_user.id,
            score=score,
            level=level,
            details=details,
        )
        await stress_collection.insert_one(result.dict())
        await callback.message.answer(
            f"{STRESS_COMPLETED}\nҰпай: {score}/{len(STRESS_QUESTIONS)}\nДеңгей: {level.title()}",
            reply_markup=back_to_menu_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return
    await state.update_data(index=index, score=score, details=details)
    await callback.message.answer(STRESS_QUESTIONS[index], reply_markup=stress_keyboard())
    await callback.answer()


@router.message(Command("panic"))
async def cmd_panic(message: Message) -> None:
    await message.answer(PANIC_INTRO)
    for step in PANIC_BREATHING_STEPS:
        await asyncio.sleep(1)
        await message.answer(step)
    for step in PANIC_GROUNDING_STEPS:
        await asyncio.sleep(1)
        await message.answer(step)


@router.message(Command("breath"))
async def cmd_breath(message: Message) -> None:
    await message.answer(BREATH_INTRO)
    for step in BREATH_STEPS:
        await asyncio.sleep(1)
        await message.answer(step)
