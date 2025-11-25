from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

MOOD_OPTIONS = [
    ("😊 Өте жақсы", "great"),
    ("🙂 Жақсы", "fine"),
    ("😐 Жәй", "okay"),
    ("😞 Жаман", "bad"),
    ("😡 Ашулы", "angry"),
    ("😴 Шаршаған", "tired"),
]

CAUSE_OPTIONS = [
    ("Жұмыс", "work"),
    ("Оқу", "study"),
    ("Ұйқы", "sleep"),
    ("Қатынас", "relationship"),
    ("Отбасы", "family"),
    ("Белгісіз", "unknown"),
]

STRESS_OPTIONS = [
    ("Иә", "yes"),
    ("Жоқ", "no"),
]

MOOD_LABELS = {value: label for label, value in MOOD_OPTIONS}
CAUSE_LABELS = {value: label for label, value in CAUSE_OPTIONS}
CAUSE_LABELS.update({"scale": "Шкала бойынша"})
STRESS_LABELS = {value: label for label, value in STRESS_OPTIONS}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🌡️  Стресс тесті")
    builder.button(text="🧬  Интроверт/Экстраверт")
    builder.button(text="🔥 Мотивация түрі")
    builder.button(text="💼 Қай мамандық?")
    builder.button(text="🤖 CHAT AI")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def mood_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in MOOD_OPTIONS:
        builder.button(text=text, callback_data=f"mood:{value}")
    builder.adjust(2)
    return builder.as_markup()


def cause_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in CAUSE_OPTIONS:
        builder.button(text=text, callback_data=f"cause:{value}")
    builder.adjust(2)
    return builder.as_markup()


def stress_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in STRESS_OPTIONS:
        builder.button(text=text, callback_data=f"stress:{value}")
    builder.adjust(2)
    return builder.as_markup()


def back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🏠 Басты мәзір")
    return builder.as_markup(resize_keyboard=True)


def quiz_answer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Иә", callback_data="quiz_answer:yes")
    builder.button(text="Жоқ", callback_data="quiz_answer:no")
    builder.adjust(2)
    return builder.as_markup()
