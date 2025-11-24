from aiogram.fsm.state import State, StatesGroup


class AppStates(StatesGroup):
    """Қосымшаның негізгі күйлері."""

    idle = State()
    quiz = State()
    chat = State()
