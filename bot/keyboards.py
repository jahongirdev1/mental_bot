from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from typing import Dict

from utils.texts import (
    get_back_to_menu_label,
    get_cause_options,
    get_language_options,
    get_menu_buttons,
    get_mood_options,
    get_quiz_answer_options,
    get_stress_options,
    get_text,
)


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for text in get_menu_buttons(language):
        builder.button(text=text)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def mood_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in get_mood_options(language):
        builder.button(text=text, callback_data=f"mood:{value}")
    builder.adjust(2)
    return builder.as_markup()


def cause_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in get_cause_options(language):
        builder.button(text=text, callback_data=f"cause:{value}")
    builder.adjust(2)
    return builder.as_markup()


def stress_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in get_stress_options(language):
        builder.button(text=text, callback_data=f"stress:{value}")
    builder.adjust(2)
    return builder.as_markup()


def back_to_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_back_to_menu_label(language))
    return builder.as_markup(resize_keyboard=True)


def quiz_answer_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, value in get_quiz_answer_options(language):
        builder.button(text=text, callback_data=f"quiz_answer:{value}")
    builder.adjust(2)
    return builder.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, code in get_language_options():
        builder.button(text=name, callback_data=f"lang:{code}")
    builder.adjust(1)
    return builder.as_markup()


def cause_labels(language: str) -> Dict[str, str]:
    labels = {value: label for label, value in get_cause_options(language)}
    labels.update({"scale": get_text("mood_scale_label", language)})
    return labels


def stress_labels(language: str) -> Dict[str, str]:
    return {value: label for label, value in get_stress_options(language)}
