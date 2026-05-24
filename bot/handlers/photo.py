from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api_client import backend_client
from bot.states import InstructionFlow


router = Router()


@router.message(InstructionFlow.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext) -> None:
    await message.answer("Понял. Сейчас разберусь, что на фото.")
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    buffer = BytesIO()
    await message.bot.download_file(file.file_path, destination=buffer)

    uploaded = await backend_client.upload_image(
        user_id=message.from_user.id,
        data=buffer.getvalue(),
        filename=f"{photo.file_unique_id}.jpg",
    )
    await state.update_data(image_url=uploaded["image_url"], session_id=uploaded["session_id"])
    await state.set_state(InstructionFlow.waiting_goal)
    await message.answer("Вижу объект. Что хотите с ним сделать?")


@router.message(InstructionFlow.waiting_photo)
async def ask_for_photo(message: Message) -> None:
    await message.answer("Пришлите, пожалуйста, фото предмета или ситуации.")
