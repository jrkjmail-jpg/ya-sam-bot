from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, URLInputFile

from bot.api_client import backend_client
from config.settings import get_settings


router = Router()


@router.message(Command("history"))
async def history(message: Message) -> None:
    items = await backend_client.history(message.from_user.id)
    if not items:
        await message.answer("История пока пустая. Пришлите фото, и я сделаю первую инструкцию.")
        return

    lines = ["Ваши последние инструкции:"]
    for item in items[:10]:
        lines.append(f"- {item['title']} — {item['created_at'][:10]}")
    await message.answer("\n".join(lines))


async def generate_and_send_instruction(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    image_url = data["image_url"]
    user_goal = data["user_goal"]
    session_id = data["session_id"]
    confirmed_details = data.get("confirmed_details")

    await message.answer("Уточняю, как лучше показать шаги…")
    instruction = await backend_client.generate_instruction(
        {
            "user_id": message.from_user.id,
            "image_url": image_url,
            "user_goal": user_goal,
            "confirmed_details": confirmed_details,
            "session_id": session_id,
        }
    )

    await message.answer(_format_instruction_text(instruction))

    await message.answer("Создаю визуальную инструкцию…")
    images = await backend_client.generate_images(
        {
            "user_id": message.from_user.id,
            "image_url": image_url,
            "instruction": instruction,
            "session_id": session_id,
        }
    )

    for item in images["step_images"]:
        await message.answer_photo(_telegram_file(item["image_url"]), caption=f"Шаг {item['step_number']}")

    await message.answer("Собираю общий коллаж…")
    collage = await backend_client.create_collage(
        {
            "user_id": message.from_user.id,
            "title": instruction["title"],
            "object_image_url": image_url,
            "step_images": images["step_images"],
            "instruction_plan": instruction,
            "session_id": session_id,
        }
    )
    await message.answer_photo(_telegram_file(collage["collage_url"]), caption="Готово. Вот как это сделать самому.")
    await state.clear()


def _format_instruction_text(instruction: dict) -> str:
    lines = [
        "Готово. Я сделал инструкцию по шагам.",
        "",
        instruction["title"],
        instruction["short_summary"],
    ]
    if instruction.get("safety_notes"):
        lines.append("")
        lines.append("Важно:")
        lines.extend(f"- {note}" for note in instruction["safety_notes"])
    lines.append("")
    lines.append("Шаги:")
    for step in instruction["steps"]:
        lines.append(f"{step['step_number']}. {step['title']} — {step['description']}")
    return "\n".join(lines)


def _telegram_file(url: str) -> FSInputFile | URLInputFile:
    settings = get_settings()
    parsed = urlparse(url)
    local_path: Path | None = None
    if parsed.path.startswith("/storage/"):
        local_path = settings.storage_dir / parsed.path.removeprefix("/storage/")
    if local_path and local_path.exists():
        return FSInputFile(local_path)
    return URLInputFile(url)
