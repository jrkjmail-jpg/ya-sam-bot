from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api_client import backend_client
from bot.handlers.instruction import generate_and_send_instruction
from bot.states import InstructionFlow


router = Router()


@router.message(InstructionFlow.waiting_goal, F.text)
async def handle_goal(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    image_url = data.get("image_url")
    session_id = data.get("session_id")
    if not image_url or not session_id:
        await state.set_state(InstructionFlow.waiting_photo)
        await message.answer("Давайте начнем заново. Пришлите фото предмета.")
        return

    user_goal = message.text.strip()
    await state.update_data(user_goal=user_goal)
    await message.answer("Анализирую объект…")
    analysis = await backend_client.analyze(
        {
            "user_id": message.from_user.id,
            "image_url": image_url,
            "user_goal": user_goal,
            "session_id": session_id,
        }
    )

    if analysis["needs_clarification"] or not analysis["can_generate_instruction"]:
        await state.set_state(InstructionFlow.waiting_clarification)
        await message.answer(analysis["clarification_question"] or "Покажите еще одну важную деталь, пожалуйста.")
        return

    await generate_and_send_instruction(message, state)


@router.message(InstructionFlow.waiting_clarification)
async def handle_clarification(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    confirmed_parts: list[str] = []
    if message.text:
        confirmed_parts.append(message.text.strip())

    if message.photo:
        await message.answer("Спасибо. Проверяю важные детали…")
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        buffer = BytesIO()
        await message.bot.download_file(file.file_path, destination=buffer)
        uploaded = await backend_client.upload_image(
            user_id=message.from_user.id,
            data=buffer.getvalue(),
            filename=f"{photo.file_unique_id}.jpg",
            image_type="clarification_photo",
            session_id=data.get("session_id"),
        )
        confirmed_parts.append(f"Дополнительное фото: {uploaded['image_url']}")

    if not confirmed_parts:
        await message.answer("Напишите уточнение или пришлите дополнительное фото.")
        return

    previous = data.get("confirmed_details")
    joined = "\n".join(part for part in [previous, *confirmed_parts] if part)
    await state.update_data(confirmed_details=joined)
    await generate_and_send_instruction(message, state)
