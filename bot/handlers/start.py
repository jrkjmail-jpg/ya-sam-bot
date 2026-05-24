from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import InstructionFlow


router = Router()


START_TEXT = (
    "Привет! Я помогу сделать действие самостоятельно.\n\n"
    "Пришлите фото и напишите, что хотите сделать. "
    "Я создам простую визуальную инструкцию по шагам."
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(InstructionFlow.waiting_photo)
    await message.answer(START_TEXT)


@router.message(Command("new"))
async def new_instruction(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(InstructionFlow.waiting_photo)
    await message.answer("Хорошо. Пришлите новое фото, и я разберусь, что с ним сделать.")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Как это работает:\n"
        "1. Пришлите фото предмета или ситуации.\n"
        "2. Напишите, что хотите сделать.\n"
        "3. Я покажу простые шаги и визуальные карточки.\n\n"
        "Команды: /new — новая инструкция, /history — история."
    )
