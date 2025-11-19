from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

MOOD_OPTIONS = [
    ("😊 Great", "great"),
    ("🙂 Fine", "fine"),
    ("😐 Okay", "okay"),
    ("😞 Bad", "bad"),
    ("😡 Angry", "angry"),
    ("😴 Tired", "tired"),
]

CAUSE_OPTIONS = [
    ("Work", "work"),
    ("Study", "study"),
    ("Sleep", "sleep"),
    ("Relationship", "relationship"),
    ("Family", "family"),
    ("Unknown", "unknown"),
]

STRESS_OPTIONS = [
    ("Yes", "yes"),
    ("No", "no"),
]

MOOD_LABELS = {value: label for label, value in MOOD_OPTIONS}
CAUSE_LABELS = {value: label for label, value in CAUSE_OPTIONS}


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
    builder.button(text="Back to menu", callback_data="menu:back")
    return builder.as_markup()
