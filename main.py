"""Телеграмдағы ментал-сауықтыру боты (қазақша).
Бұл файлда барлық логика бір жерде жиналған.
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from typing import List, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

# ------------------------- Конфигурация -------------------------
# Қоршаған орта айнымалыларын жүктеу
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI клиентін дайындау
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Жауаптың негізгі жүйелік промпты
system_prompt = (
    "Сен қазақ тілінде сөйлейтін CBT стиліндегі мейірімді көмекші психологсың. "
    "Әрдайым эмоция → себеп → кеңес (3 тармақ) → қолдау форматын сақта. "
    "Диагноз қойма, қысқа әрі анық бол, қауіпсіздік туралы хабарламаны қажет болғанда қос. "
    "Өз-өзіне зиян келтіру, суицид, зорлық туралы мәтін байқалса, дереу жергілікті көмекке "
    "жүгіну туралы қауіпсіздік нұсқаулығын қос." 
)

# Mood tracking үшін SQLite файлы
DB_PATH = "mood.db"


# ------------------------- Көмекші функциялар -------------------------
async def init_db() -> None:
    """Mood трекерге арналған кестені құру."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_mood(chat_id: int, score: int, note: str | None) -> None:
    """Mood мәнін дерекқорға жазу."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mood_entries (chat_id, score, note, created_at) VALUES (?, ?, ?, ?)",
        (chat_id, score, note, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def fetch_recent_moods(chat_id: int, limit: int = 5) -> List[Tuple[int, str, str]]:
    """Соңғы mood жазбаларын алу."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT score, COALESCE(note, ''), created_at FROM mood_entries WHERE chat_id = ? "
        "ORDER BY created_at DESC LIMIT ?",
        (chat_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


async def ask_openai(user_prompt: str) -> str:
    """OpenAI-ға сұраныс жасап, форматталған жауап алу."""
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=450,
    )
    return response.choices[0].message.content or "Кешіріңіз, жауап бере алмадым."


# ------------------------- Мемлекеттік машиналар -------------------------
class MoodStates(StatesGroup):
    waiting_score = State()
    waiting_note = State()


class StressTestStates(StatesGroup):
    answering = State()


# ------------------------- Хэндлерлер -------------------------
async def cmd_start(message: Message) -> None:
    """Ботпен таныстыру."""
    text = (
        "Сәлем! Мен ментал-сауықтыруға арналған қазақша ассистентпін.\n\n"
        "AI функциялары:\n"
        "• /ai + мәтін — CBT стиліндегі кеңес алу\n"
        "• /emo + мәтін — эмоцияны анықтау\n"
        "• /reframe + ой — теріс ойды қайта қарау\n"
        "• /decision + мәселе — 3-қадамдық шешім\n"
        "• /stress_ai + мәтін — стресс деңгейін бағалау\n\n"
        "Non-AI құралдар:\n"
        "• /mood — 1-10 шкаламен көңіл-күй жазу\n"
        "• /stress_test — 7 сұрақтық стресс тест\n"
        "• /selfcare — күнделікті өзін-өзі күтім идеялары\n"
        "• /breath — 4-7-8 тыныс жаттығуы\n"
        "• /grounding — 5-4-3-2-1 әдісі\n"
        "• /journal — жазбалық сұрақтар\n"
        "• /faq — жиі сұрақтар\n"
        "• /safety — қауіпсіздік ережесі\n\n"
        "Қай функцияны қолданғыңыз келсе, сәйкес команданы жазыңыз."
    )
    await message.answer(text)


async def cmd_ai(message: Message, command: CommandObject | None = None) -> None:
    """AI-психолог чат."""
    user_text = command.args if command else None
    if not user_text:
        await message.answer("Қандай ой мазалайды? /ai кейін мәтінді жазыңыз.")
        return
    reply = await ask_openai(user_text)
    await message.answer(reply)


async def cmd_emotion(message: Message, command: CommandObject | None = None) -> None:
    """Эмоция классификациясы."""
    user_text = command.args if command else None
    if not user_text:
        await message.answer("Эмоцияны анықтау үшін /emo кейін мәтін жазыңыз.")
        return
    prompt = (
        "Эмоцияны, себепті және қысқа қолдауды бер. Формат сақталсын. Мәтін: "
        f"{user_text}"
    )
    reply = await ask_openai(prompt)
    await message.answer(reply)


async def cmd_reframe(message: Message, command: CommandObject | None = None) -> None:
    """Теріс ойды қайта қарау."""
    user_text = command.args if command else None
    if not user_text:
        await message.answer("Теріс ойды жазып жіберіңіз: /reframe ой")
        return
    prompt = (
        "Теріс ойды CBT тәсілімен қайта құрыңыз. Формат: эмоция, себеп, 3 кеңес, қолдау. "
        f"Ой: {user_text}"
    )
    reply = await ask_openai(prompt)
    await message.answer(reply)


async def cmd_decision(message: Message, command: CommandObject | None = None) -> None:
    """3-қадамдық шешім жасау."""
    user_text = command.args if command else None
    if not user_text:
        await message.answer("Қандай мәселені шешкіміз келеді? /decision кейін жазыңыз.")
        return
    prompt = (
        "Проблеманы шешуге арналған 3 нақты қадам ұсын. Әр қадамда қысқа әрекет болсын. "
        "Формат: эмоция, себеп, кеңес (3 тармақ), қолдау. Мәселе: "
        f"{user_text}"
    )
    reply = await ask_openai(prompt)
    await message.answer(reply)


async def cmd_stress_ai(message: Message, command: CommandObject | None = None) -> None:
    """AI арқылы стресс деңгейін бағалау."""
    user_text = command.args if command else None
    if not user_text:
        await message.answer("Стресс туғызатын жағдайды сипаттаңыз: /stress_ai мәтін")
        return
    prompt = (
        "Мәтінді оқып, стресс/мазасыздық деңгейін (төмен/орташа/жоғары) атап, қысқа себеп пен 3 кеңес бер. "
        f"Мәтін: {user_text}"
    )
    reply = await ask_openai(prompt)
    await message.answer(reply)


async def cmd_mood(message: Message, state: FSMContext) -> None:
    """Mood tracking бастау."""
    await state.set_state(MoodStates.waiting_score)
    await message.answer("Көңіл-күйді 1-10 аралығында бағалаңыз (10 — өте жақсы).")


async def mood_score_received(message: Message, state: FSMContext) -> None:
    """Пайдаланушының mood балын қабылдау."""
    try:
        score = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Сан енгізіңіз: 1-10.")
        return
    if score < 1 or score > 10:
        await message.answer("Диапазон 1-10 арасында болуы керек.")
        return
    await state.update_data(score=score)
    await state.set_state(MoodStates.waiting_note)
    await message.answer("Қысқаша жазба қалдырасыз ба? Жай мәтін жазыңыз немесе /skip деп өткізіңіз.")


async def mood_note_received(message: Message, state: FSMContext) -> None:
    """Mood жазбасын аяқтау."""
    data = await state.get_data()
    score = data.get("score")
    note = None if message.text == "/skip" else message.text
    save_mood(message.chat.id, score, note)
    await state.clear()

    recent = fetch_recent_moods(message.chat.id)
    history = "\n".join(
        [f"{idx+1}. {row[0]} балл — {row[1]} ({row[2][:16]})" for idx, row in enumerate(recent)]
    )
    await message.answer(
        "Жазылды! Соңғы жазбалар:\n" + (history or "Бос."),
    )


async def cmd_selfcare(message: Message) -> None:
    """Күнделікті өзін-өзі күтім тапсырмалары."""
    tasks = [
        "5 минут тыныс жаттығуы",
        "10 минут таза ауада серуен",
        "1 стақан су ішу",
        "Рахмет айтатын 3 нәрсені жазу",
        "Телефонсыз 15 минут демалу",
        "Бір жақын адамға хабарласу",
    ]
    formatted = "\n".join([f"• {t}" for t in tasks])
    await message.answer("Бүгінгі өзін-өзі күтім идеялары:\n" + formatted)


async def cmd_breath(message: Message) -> None:
    """4-7-8 тыныс жаттығуы."""
    text = (
        "4-7-8 тыныс техникасы:\n"
        "1) 4 секунд мұрынмен терең дем алыңыз;\n"
        "2) 7 секунд тынысты ұстап тұрыңыз;\n"
        "3) 8 секунд ауызбен баяу шығарыңыз;\n"
        "4) 4-8 рет қайталаңыз. Үнсіз, ыңғайлы қалыпта жасаңыз."
    )
    await message.answer(text)


async def cmd_grounding(message: Message) -> None:
    """5-4-3-2-1 grounding әдісі."""
    text = (
        "5-4-3-2-1 grounding:\n"
        "5 көруге болатын нәрсе;\n"
        "4 сезіне алатын зат;\n"
        "3 естіп тұрған дыбыс;\n"
        "2 иіс;\n"
        "1 дәм.\n"
        "Әр пунктті атай отырып, тыныс алуыңызды байқап көріңіз."
    )
    await message.answer(text)


async def cmd_journal(message: Message) -> None:
    """Журнал сұрақтары."""
    questions = [
        "Бүгінгі көңіл-күйімді не жақсартты?",
        "Бүгін қандай қиындық болды және не үйрендім?",
        "Өзімді қолдау үшін қазір не істей аламын?",
        "Мен үшін маңызды адамдар кім және неге?",
        "Қандай шекараны сақтағым келеді?",
    ]
    await message.answer("Жазбалық сұрақтар:\n" + "\n".join([f"• {q}" for q in questions]))


async def cmd_faq(message: Message) -> None:
    """FAQ бөлімі."""
    text = (
        "Жиі сұрақтар:\n"
        "• Бұл медициналық диагноз емес, тек қолдау.\n"
        "• Деректер тек mood трекерде локалды сақталады.\n"
        "• AI жауаптары қысқа, қазақша және CBT стилінде.\n"
        "• Қауіпті мәтін болса, қауіпсіздік хабарламасы беріледі."
    )
    await message.answer(text)


async def cmd_safety(message: Message) -> None:
    """Қауіпсіздік режимі."""
    text = (
        "Қауіпсіздік: егер өз-өзіңізге зиян келтіру ойы болса, дереу 112/103-ке хабарласыңыз,"
        " жақын адамға айтыңыз немесе жергілікті дәрігерге барыңыз. Сіз жалғыз емессіз."
    )
    await message.answer(text)


# ------------------------- Стресс тест -------------------------
stress_questions = [
    "1) Соңғы аптада өзінізді жиі мазасыз сезіндіңіз бе? (1-5)",
    "2) Ұйқыңыз бұзылды ма немесе оянған соң шаршайсыз ба? (1-5)",
    "3) Қатты ашулану немесе ширығу байқала ма? (1-5)",
    "4) Нақтылай алмайтын жағымсыз ойлар мазалай ма? (1-5)",
    "5) Дене кернеуі (иық, мойын) сезілетін кездер көп пе? (1-5)",
    "6) Демалысқа уақыт бөлу қиын ба? (1-5)",
    "7) Аппетит немесе көңілсіздік өзгерді ме? (1-5)",
]


async def cmd_stress_test(message: Message, state: FSMContext) -> None:
    """Стресс тестті бастау."""
    await state.set_state(StressTestStates.answering)
    await state.update_data(index=0, scores=[])
    await message.answer(
        "7 сұраққа 1-5 баллмен жауап беріңіз (1 — мүлде жоқ, 5 — өте жиі).\n" + stress_questions[0]
    )


async def stress_test_answer(message: Message, state: FSMContext) -> None:
    """Стресс тест сұрақтарына жауап қабылдау."""
    try:
        score = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Сан енгізіңіз: 1-5")
        return
    if score < 1 or score > 5:
        await message.answer("Диапазон 1-5 арасында болуы керек.")
        return

    data = await state.get_data()
    index = data.get("index", 0)
    scores: List[int] = data.get("scores", [])
    scores.append(score)

    if index + 1 >= len(stress_questions):
        await state.clear()
        total = sum(scores)
        avg = total / len(stress_questions)
        if avg < 2:
            level = "Төмен стресс"
        elif avg < 3.5:
            level = "Орташа стресс"
        else:
            level = "Жоғары стресс"
        await message.answer(
            f"Тест аяқталды! Орташа балл: {avg:.2f}. Деңгей: {level}.\n"
            "Қысқаша кеңес: тыныс жаттығуы, шағын үзіліс, қолдау сұрау."
        )
    else:
        index += 1
        await state.update_data(index=index, scores=scores)
        await message.answer(stress_questions[index])


# ------------------------- Жалпы AI жауабы -------------------------
async def fallback_ai(message: Message) -> None:
    """Әдепкі AI чаты."""
    prompt = (
        "Пайдаланушының мәтініне CBT стиліндегі қысқа жауап бер. Форматты сақта. Мәтін: "
        f"{message.text}"
    )
    reply = await ask_openai(prompt)
    await message.answer(reply)


async def on_error(update, error) -> None:
    """Жалпы қате өңдеуші."""
    logging.exception("Қате кездесті: %s", error)
    if isinstance(update, Message):
        await update.answer("Кешіріңіз, техникалық ақау шықты. Кейінірек қайталап көріңіз.")


# ------------------------- Негізгі қосымшаны іске қосу -------------------------
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN орнатылмаған.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY орнатылмаған.")

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Командалар
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_ai, Command("ai"))
    dp.message.register(cmd_emotion, Command("emo"))
    dp.message.register(cmd_reframe, Command("reframe"))
    dp.message.register(cmd_decision, Command("decision"))
    dp.message.register(cmd_stress_ai, Command("stress_ai"))
    dp.message.register(cmd_mood, Command("mood"))
    dp.message.register(cmd_selfcare, Command("selfcare"))
    dp.message.register(cmd_breath, Command("breath"))
    dp.message.register(cmd_grounding, Command("grounding"))
    dp.message.register(cmd_journal, Command("journal"))
    dp.message.register(cmd_faq, Command("faq"))
    dp.message.register(cmd_safety, Command("safety"))
    dp.message.register(cmd_stress_test, Command("stress_test"))

    # Mood FSM
    dp.message.register(mood_score_received, MoodStates.waiting_score)
    dp.message.register(mood_note_received, MoodStates.waiting_note)

    # Стресс тест FSM
    dp.message.register(stress_test_answer, StressTestStates.answering)

    # Әдепкі AI жауап
    dp.message.register(fallback_ai, F.text)

    # Қате өңдеу
    dp.errors.register(on_error)

    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot іске қосылуда...")
    asyncio.run(main())
