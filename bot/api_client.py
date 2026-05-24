from __future__ import annotations

import httpx

from config.settings import get_settings


class BackendClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.api_base_url.rstrip("/")

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
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{self.base_url}/upload-image", data=form, files=files)
            response.raise_for_status()
            return response.json()

    async def analyze(self, payload: dict) -> dict:
        return await self._post("/analyze", payload, timeout=120)

    async def generate_instruction(self, payload: dict) -> dict:
        return await self._post("/generate-instruction", payload, timeout=180)

    async def generate_images(self, payload: dict) -> dict:
        return await self._post("/generate-images", payload, timeout=600)

    async def create_collage(self, payload: dict) -> dict:
        return await self._post("/create-collage", payload, timeout=180)

    async def history(self, user_id: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(f"{self.base_url}/instructions/{user_id}")
            response.raise_for_status()
            return response.json()

    async def _post(self, path: str, payload: dict, timeout: int) -> dict:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()


backend_client = BackendClient()
