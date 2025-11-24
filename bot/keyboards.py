from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🟩 Стресс тесті", callback_data="quiz:stress_level")
    builder.button(text="🟩 Интроверт/Экстраверт", callback_data="quiz:personality")
    builder.button(text="🟨 Мотивация түрі", callback_data="quiz:motivation")
    builder.button(text="🟥 Қай мамандық?", callback_data="quiz:career")
    builder.button(text="💬 CHAT AI", callback_data="menu:chat")
    builder.adjust(1)
    return builder.as_markup()


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


def quiz_answer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Иә", callback_data="quiz_answer:yes")
    builder.button(text="Жоқ", callback_data="quiz_answer:no")
    builder.adjust(2)
    return builder.as_markup()
