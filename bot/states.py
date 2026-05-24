from aiogram.fsm.state import State, StatesGroup


class InstructionFlow(StatesGroup):
    waiting_photo = State()
    waiting_goal = State()
    waiting_clarification = State()
