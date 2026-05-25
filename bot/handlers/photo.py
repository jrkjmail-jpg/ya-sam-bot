import asyncio
from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api_client import backend_client
from bot.keyboards.object_confirmation import object_confirmation_keyboard
from bot.states import InstructionFlow


router = Router()
MEDIA_GROUP_DELAY_SECONDS = 1.2
media_group_tasks: dict[str, asyncio.Task] = {}
photo_locks: dict[int, asyncio.Lock] = {}


@router.message(InstructionFlow.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext) -> None:
    if message.media_group_id:
        await _store_photo(message, state)
        task_key = f"{message.chat.id}:{message.media_group_id}"
        previous_task = media_group_tasks.get(task_key)
        if previous_task and not previous_task.done():
            previous_task.cancel()
        media_group_tasks[task_key] = asyncio.create_task(_process_media_group(message, state, task_key))
        return

    await message.answer("Понял. Сейчас внимательно посмотрю фото и определю объект.")
    await _store_photo(message, state)
    await _identify_and_ask_confirmation(message, state)


async def _process_media_group(message: Message, state: FSMContext, task_key: str) -> None:
    try:
        await asyncio.sleep(MEDIA_GROUP_DELAY_SECONDS)
        await message.answer("Получил несколько фото. Анализирую их как один объект…")
        await _identify_and_ask_confirmation(message, state)
    finally:
        media_group_tasks.pop(task_key, None)


async def _store_photo(message: Message, state: FSMContext) -> None:
    lock = photo_locks.setdefault(message.chat.id, asyncio.Lock())
    async with lock:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        buffer = BytesIO()
        await message.bot.download_file(file.file_path, destination=buffer)

        uploaded = await backend_client.upload_image(
            user_id=message.from_user.id,
            data=buffer.getvalue(),
            filename=f"{photo.file_unique_id}.jpg",
            session_id=(await state.get_data()).get("session_id"),
        )
        data = await state.get_data()
        image_urls = list(data.get("image_urls", []))
        image_urls.append(uploaded["image_url"])
        await state.update_data(
            image_url=image_urls[0],
            image_urls=image_urls,
            session_id=uploaded["session_id"],
        )


async def _identify_and_ask_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    image_urls = data.get("image_urls") or ([data["image_url"]] if data.get("image_url") else [])
    if not image_urls:
        await message.answer("Пришлите, пожалуйста, фото предмета или ситуации.")
        return

    analysis = await backend_client.identify_object(
        {
            "user_id": message.from_user.id,
            "image_url": image_urls[0],
            "image_urls": image_urls,
            "session_id": data.get("session_id"),
        }
    )
    detected_object = analysis.get("detected_object") or "предмет на фото"
    confidence = analysis.get("confidence")
    await state.update_data(detected_object=detected_object, object_analysis=analysis)
    await state.set_state(InstructionFlow.waiting_object_confirmation)

    confidence_text = f" Уверенность: {round(confidence * 100)}%." if isinstance(confidence, (int, float)) else ""
    await message.answer(
        f"Похоже, главный объект: {detected_object}.{confidence_text}\n\nЭто тот объект, для которого нужна инструкция?",
        reply_markup=object_confirmation_keyboard(),
    )


@router.message(InstructionFlow.waiting_photo)
async def ask_for_photo(message: Message) -> None:
    await message.answer("Пришлите, пожалуйста, фото предмета или ситуации.")
