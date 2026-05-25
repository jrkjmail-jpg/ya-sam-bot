from __future__ import annotations

from pathlib import Path

import httpx

from config.settings import get_settings
from database.models import SessionStatus, StoredImageType
from database.repositories import (
    add_image,
    create_instruction,
    create_instruction_session,
    list_user_instructions,
    set_instruction_collage,
    update_instruction_session,
    upsert_user,
)
from database.session import SessionLocal
from services.collage_service import collage_service
from services.image_generation_service import image_generation_service
from services.instruction_service import instruction_service
from services.storage_service import storage_service
from services.vision_service import vision_service


class BackendClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.effective_api_base_url.rstrip("/")

    async def upload_image(
        self,
        user_id: int,
        data: bytes,
        filename: str,
        image_type: str = "source_photo",
        session_id: int | None = None,
    ) -> dict:
        form = {"user_id": str(user_id), "image_type": image_type}
        if session_id:
            form["session_id"] = str(session_id)
        files = {"file": (filename, data, "image/jpeg")}
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(f"{self.base_url}/upload-image", data=form, files=files)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return self._local_upload_image(user_id, data, filename, image_type, session_id)

    async def analyze(self, payload: dict) -> dict:
        try:
            return await self._post("/analyze", payload, timeout=120)
        except httpx.HTTPError:
            return self._local_analyze(payload)

    async def identify_object(self, payload: dict) -> dict:
        try:
            return await self._post("/identify-object", payload, timeout=120)
        except httpx.HTTPError:
            return self._local_identify_object(payload)

    async def generate_instruction(self, payload: dict) -> dict:
        try:
            return await self._post("/generate-instruction", payload, timeout=180)
        except httpx.HTTPError:
            return self._local_generate_instruction(payload)

    async def generate_images(self, payload: dict) -> dict:
        try:
            return await self._post("/generate-images", payload, timeout=600)
        except httpx.HTTPError:
            return self._local_generate_images(payload)

    async def create_collage(self, payload: dict) -> dict:
        try:
            return await self._post("/create-collage", payload, timeout=180)
        except httpx.HTTPError:
            return self._local_create_collage(payload)

    async def history(self, user_id: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(f"{self.base_url}/instructions/{user_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return self._local_history(user_id)

    async def _post(self, path: str, payload: dict, timeout: int) -> dict:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()

    def _local_upload_image(
        self,
        user_id: int,
        data: bytes,
        filename: str,
        image_type: str,
        session_id: int | None,
    ) -> dict:
        with SessionLocal() as db:
            user = upsert_user(db, telegram_id=user_id)
            if session_id is None:
                session = create_instruction_session(db, user_id=user.id, status=SessionStatus.waiting_goal.value)
                session_id = session.id
            suffix = Path(filename or "photo.jpg").suffix or ".jpg"
            image_url = storage_service.save_bytes(data, "photos", suffix)
            add_image(db, session_id=session_id, image_type=image_type, url=image_url)
            return {"image_url": image_url, "session_id": session_id}

    def _local_analyze(self, payload: dict) -> dict:
        image_input = payload.get("image_urls") or payload["image_url"]
        analysis = vision_service.analyze(image_input, payload["user_goal"])
        session_id = payload.get("session_id")
        if session_id:
            with SessionLocal() as db:
                update_instruction_session(
                    db,
                    session_id,
                    status=(
                        SessionStatus.waiting_clarification.value
                        if analysis.get("needs_clarification")
                        else SessionStatus.generating_instruction.value
                    ),
                    detected_object=analysis.get("detected_object"),
                    confidence=analysis.get("confidence"),
                    user_goal=payload["user_goal"],
                )
        return analysis

    def _local_identify_object(self, payload: dict) -> dict:
        image_urls = payload.get("image_urls") or ([payload["image_url"]] if payload.get("image_url") else [])
        analysis = vision_service.identify(image_urls)
        session_id = payload.get("session_id")
        if session_id:
            with SessionLocal() as db:
                update_instruction_session(
                    db,
                    session_id,
                    status=SessionStatus.waiting_goal.value,
                    detected_object=analysis.get("detected_object"),
                    confidence=analysis.get("confidence"),
                )
        return analysis

    def _local_generate_instruction(self, payload: dict) -> dict:
        instruction = instruction_service.generate(
            payload["image_url"],
            payload["user_goal"],
            payload.get("confirmed_details"),
            payload.get("analysis"),
        )
        session_id = payload.get("session_id")
        if session_id:
            with SessionLocal() as db:
                create_instruction(
                    db,
                    session_id=session_id,
                    title=instruction["title"],
                    short_summary=instruction["short_summary"],
                    steps=instruction["steps"],
                )
                update_instruction_session(db, session_id, status=SessionStatus.generating_images.value)
            instruction["session_id"] = session_id
        return instruction

    def _local_generate_images(self, payload: dict) -> dict:
        instruction = payload.get("instruction_plan") or payload["instruction"]
        steps = instruction["steps"]
        step_images = image_generation_service.generate_step_images(payload["image_url"], steps)
        session_id = payload.get("session_id")
        if session_id:
            with SessionLocal() as db:
                for item in step_images:
                    add_image(db, session_id, StoredImageType.step_card.value, item["image_url"])
        return {"step_images": step_images}

    def _local_create_collage(self, payload: dict) -> dict:
        collage_url = collage_service.create_collage(
            payload["title"],
            payload["step_images"],
            instruction_plan=payload.get("instruction_plan"),
            original_image_url=payload.get("object_image_url"),
        )
        session_id = payload.get("session_id")
        if session_id:
            with SessionLocal() as db:
                add_image(db, session_id, StoredImageType.collage.value, collage_url)
                set_instruction_collage(db, session_id, collage_url)
                update_instruction_session(db, session_id, status=SessionStatus.completed.value)
        return {"collage_url": collage_url}

    def _local_history(self, user_id: int) -> list[dict]:
        with SessionLocal() as db:
            user = upsert_user(db, telegram_id=user_id)
            items = list_user_instructions(db, user.id)
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "short_summary": item.short_summary,
                    "collage_url": item.collage_url,
                    "created_at": item.created_at.isoformat(),
                }
                for item in items
            ]


backend_client = BackendClient()
