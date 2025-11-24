from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
STRESS_LABELS = {value: label for label, value in STRESS_OPTIONS}


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


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Басты мәзір", callback_data="menu:back")
    return builder.as_markup()
