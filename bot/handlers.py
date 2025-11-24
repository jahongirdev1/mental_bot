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
    STRESS_LABELS,
    back_to_menu_keyboard,
    cause_keyboard,
    main_menu_keyboard,
    mood_keyboard,
    quiz_answer_keyboard,
    stress_keyboard,
)
from bot.states import AppStates
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


QUIZZES: dict[str, dict[str, object]] = {
    "stress_level": {
        "title": "1-Ойын: Стресс деңгейін анықтау тесті",
        "badge": "🟩",
        "questions": [
            "Соңғы күндері өзіңізді жиі шаршаңқы сезінесіз бе?",
            "Қарапайым тапсырмалардың өзі ауыр болып көріне ме?",
            "Ұйқыңыздың сапасы төмендеп кетті ме?",
            "Кешке басыңыз жиі ауыра ма?",
            "Ұсақ мәселелерге тез ашуланып қаласыз ба?",
            "Уақыт ештеңеге жетпей жатқандай сезілетін кездер бола ма?",
            "Артық уайымдайсыз ба?",
            "Ештеңеге көңіл-күй болмай қалатын күндер бола ма?",
            "Демалғаннан кейін де шаршау басылмай ма?",
            "Күн ішінде зейін қою қиынға соға ма?",
        ],
        "ranges": [
            (3, "Төмен стресс", "Ұпай аз – күш-қуатыңыз жақсы. Режимді сақтап, демалысты ұмытпаңыз."),
            (6, "Орташа стресс", "Аздап шаршау бар. Кішкентай үзілістер, жеңіл жаттығу мен ұйқы тәртібі көмектеседі."),
            (10, "Жоғары стресс", "Күшті стресс байқалады. Жұмысты жеңілдету, демалыс жоспарлау және қажет болса маманға жүгіну маңызды."),
        ],
    },
    "personality": {
        "title": "2-Ойын: Интроверт пе, экстраверт пе?",
        "badge": "🟩",
        "questions": [
            "Жалғыз өткізетін уақыт сізге ұнай ма?",
            "Көп адаммен бірге болу сізді шаршата ма?",
            "Жаңа адамдармен танысу оңай ма?",
            "Мерекелерде көпшіліктің ортасында жүруді ұнатасыз ба?",
            "Телефон қоңырауынан қашатын кездеріңіз бола ма?",
            "Әңгіме бастау сізге оңай ма?",
            "Жалғыз қалу сізге энергия береді ме?",
            "Топпен жұмыс істегенді жақсы көресіз бе?",
            "Өз сезімдеріңізді білдіру қиынға соға ма?",
            "Алдын ала жоспарсыз, кенеттен бір нәрсе жасауды ұнатасыз ба?",
        ],
        "ranges": [
            (3, "Көбірек экстраверт", "Әңгіме мен адамдардан күш аласыз. Топтық жобалар мен коммуникация қажет салалар сай келеді."),
            (6, "Амбиверт", "Екі жаққа да бейімсіз: жалғыздық пен компанияны тең ұнатасыз. Жұмыс таңдағанда тепе-теңдік жасаңыз."),
            (10, "Көбірек интроверт", "Тыныш орта мен жеке жұмысқа бейімсіз. Жұмысты жоспарлап, демалысқа уақыт бөліп отырыңыз."),
        ],
    },
    "motivation": {
        "title": "3-Ойын: Мотивация түрін анықтау (ішкі/сыртқы)",
        "badge": "🟨",
        "questions": [
            "Тапсырма орындауда ең маңыздысы – нәтиже деп ойлайсыз ба?",
            "Мақтау естігенде көбірек ынталанасыз ба?",
            "Жаңа нәрсе үйрену сізге қызық па?",
            "Сыйлық болмаса жұмыс істеу қиын ба?",
            "Мақсат қоюды жақсы көресіз бе?",
            "Процестен гөрі нәтижені маңызды санайсыз ба?",
            "Өз дамуыңыз үшін қиын тапсырмалар алуға дайынсыз ба?",
            "Біреулер күткені үшін жұмыс істейтін кезіңіз бола ма?",
            "Өзіңізді жетілдіруге бағытталған істер мотивация береді ме?",
            "Нәтиже тез көрінбесе, қызығушылық тез сөне ме?",
        ],
        "ranges": [
            (3, "Ішкі мотивация басым", "Үйрену мен даму сізді алға жетелейді. Жеке мақсат қойып, прогресті бақылаңыз."),
            (6, "Аралас мотивация", "Ішкі де, сыртқы да ынталандыру әсер етеді. Екеуін тең ұштастырып, өзіңізді марапаттауды ұмытпаңыз."),
            (10, "Сыртқы мотивация басым", "Қарапайым сыйақы мен кері байланыс маңызды. Нәтижені бөлшектеп, аралық жетістіктерге сый жасаңыз."),
        ],
    },
    "career": {
        "title": "4-Ойын: Саған қай мамандық сәйкес келеді? (Мини-карьера тест)",
        "badge": "🟥",
        "questions": [
            "Адамдармен жұмыс істеу сізге ұнай ма?",
            "Техника мен бағдарламалауға қызығасыз ба?",
            "Командада жұмыс істеу ыңғайлы ма?",
            "Графикалық дизайнға қызығуыңыз бар ма?",
            "Сөйлеп, презентация жасағанды ұнатасыз ба?",
            "Мәселелерді шешу сізді қызықтыра ма?",
            "Санмен жұмыс істеу ұнай ма?",
            "Жаңа идеялар ойлап табу қолыңыздан келе ме?",
            "Тәртіп пен нақты жоспар сізге маңызды ма?",
            "Бір уақытта бірнеше істі қатар атқара аласыз ба?",
        ],
        "ranges": [
            (3, "Шығармашылық/бейтарап бағыт", "Бірнеше саланы байқап көру керек. Хобби форматында тест жасап, өзіңізге ұнайтын бағытты белгілеңіз."),
            (6, "Теңгерімді әмбебаптығыңыз бар", "Жоба менеджменті, өнім дайындау немесе аналитика сияқты аралас салаларға бейімсіз."),
            (10, "Адамдармен және идеямен жұмыс", "Коммуникация, дизайн не IT жобалары сай келеді. Өзекті курстарды қарап, шағын пилот жобадан бастаңыз."),
        ],
    },
}


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


def quiz_header(quiz_key: str) -> str:
    quiz = QUIZZES[quiz_key]
    return f"{quiz['badge']} {quiz['title']}"


def quiz_result_text(quiz_key: str, score: int, total: int) -> str:
    quiz = QUIZZES[quiz_key]
    level = ""
    advice = ""
    for max_score, label, tip in quiz["ranges"]:
        level = label
        advice = tip
        if score <= max_score:
            break
    return (
        f"{quiz_header(quiz_key)} аяқталды!\n"
        f"Ұпай: {score}/{total}\n"
        f"Нәтиже: {level}\n"
        f"Кеңес: {advice}"
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AppStates.idle)
    await message.answer(
        "Қай сервисті таңдайсыз? Тестті таңдаңыз немесе CHAT AI арқылы сөйлесіңіз.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.message(F.text == "🏠 Басты мәзір")
async def back_to_menu_button(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.message(Command("checkin"))
async def cmd_checkin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CheckInStates.mood)
    await message.answer(GREETING_TEXT, reply_markup=mood_keyboard())


@router.message(F.text == "💬 CHAT AI")
async def start_chat(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AppStates.quiz.state:
        await message.answer("Алдымен тестті аяқтаңыз.")
        return
    await state.clear()
    await state.set_state(AppStates.chat)
    await message.answer(
        "CHAT AI іске қосылды. Сұрағыңызды немесе ойыңызды жазыңыз."
        " Аяқтасаңыз, төмендегі Басты мәзірді басыңыз.",
        reply_markup=back_to_menu_keyboard(),
    )


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
    await state.set_state(AppStates.idle)
    await callback.message.answer(CHECKIN_THANKS, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.message(F.text.in_(
    [
        "🟩 Стресс тесті",
        "🟩 Интроверт/Экстраверт",
        "🟨 Мотивация түрі",
        "🟥 Қай мамандық?",
    ]
))
async def start_quiz_from_menu(message: Message, state: FSMContext) -> None:
    mapping = {
        "🟩 Стресс тесті": "stress_level",
        "🟩 Интроверт/Экстраверт": "personality",
        "🟨 Мотивация түрі": "motivation",
        "🟥 Қай мамандық?": "career",
    }
    quiz_key = mapping.get(message.text)
    await start_quiz(message, state, quiz_key)


async def start_quiz(message: Message, state: FSMContext, quiz_key: str | None = None) -> None:
    if quiz_key is None:
        return
    if quiz_key not in QUIZZES:
        await message.answer("Белгісіз тест.")
        return
    await state.clear()
    await state.set_state(AppStates.quiz)
    await state.update_data(quiz_key=quiz_key, index=0, score=0)
    quiz = QUIZZES[quiz_key]
    await message.answer(
        f"{quiz_header(quiz_key)}\n10 сұраққа Иә/Жоқ деп жауап беріңіз.",
    )
    await message.answer(quiz["questions"][0], reply_markup=quiz_answer_keyboard())


@router.callback_query(AppStates.quiz, F.data.startswith("quiz_answer:"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    quiz_key: str = data.get("quiz_key")
    index: int = data.get("index", 0)
    score: int = data.get("score", 0)
    if not quiz_key or quiz_key not in QUIZZES:
        await callback.message.answer("Тест табылмады. Басты мәзірден қайта таңдаңыз.")
        await state.clear()
        await callback.answer()
        return
    quiz = QUIZZES[quiz_key]
    answer_value = callback.data.split(":", 1)[1]
    if answer_value == "yes":
        score += 1
    index += 1
    total = len(quiz["questions"])
    if index >= total:
        result_text = quiz_result_text(quiz_key, score, total)
        await callback.message.answer(result_text, reply_markup=back_to_menu_keyboard())
        await state.clear()
        await state.set_state(AppStates.idle)
        await callback.answer()
        return
    await state.update_data(index=index, score=score, quiz_key=quiz_key)
    await callback.message.answer(quiz["questions"][index], reply_markup=quiz_answer_keyboard())
    await callback.answer()


@router.message(AppStates.quiz)
async def quiz_text_block(message: Message) -> None:
    await message.answer("Қазір тест жүріп жатыр. Иә/Жоқ батырмаларын пайдаланыңыз.")


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
        await state.set_state(AppStates.idle)
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
