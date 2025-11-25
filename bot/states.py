from aiogram.fsm.state import State, StatesGroup


class AppStates(StatesGroup):
    idle = State()
    quiz = State()
    chat = State()
