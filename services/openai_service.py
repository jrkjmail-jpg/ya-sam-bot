from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from config.settings import BASE_DIR, get_settings
from services.storage_service import storage_service


def _read_prompt(name: str) -> str:
    return (BASE_DIR / "prompts" / name).read_text(encoding="utf-8")


class OpenAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def _image_input(self, image_url: str) -> str:
        local_bytes = storage_service.get_bytes_if_local(image_url)
        if local_bytes:
            encoded = base64.b64encode(local_bytes).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
        return image_url

    def analyze_object(self, image_url: str, user_goal: str) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        prompt = _read_prompt("analyze_object_prompt.txt")
        input_payload = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"{prompt}\n\nЦель пользователя: {user_goal}"},
                    {"type": "input_image", "image_url": self._image_input(image_url)},
                ],
            }
        ]
        return self._json_response(input_payload, "yasam_object_analysis")

    def generate_instruction(self, image_url: str, user_goal: str, confirmed_details: str | None) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        prompt = _read_prompt("generate_instruction_prompt.txt")
        details = confirmed_details or "Дополнительных уточнений нет."
        input_payload = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{prompt}\n\nЦель пользователя: {user_goal}\nУточнения: {details}",
                    },
                    {"type": "input_image", "image_url": self._image_input(image_url)},
                ],
            }
        ]
        return self._json_response(input_payload, "yasam_instruction")

    def generate_step_image(self, source_image_url: str, visual_prompt: str) -> bytes:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        style = _read_prompt("image_prompt_style.txt")
        response = self.client.responses.create(
            model=self.settings.openai_text_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": f"{style}\n\nСцена шага: {visual_prompt}"},
                        {"type": "input_image", "image_url": self._image_input(source_image_url)},
                    ],
                }
            ],
            tools=[
                {
                    "type": "image_generation",
                    "action": "auto",
                    "model": self.settings.openai_image_model,
                    "size": "1024x1024",
                    "quality": "high",
                    "input_fidelity": "high",
                }
            ],
        )
        for output in response.output:
            if getattr(output, "type", None) == "image_generation_call" and getattr(output, "result", None):
                return base64.b64decode(output.result)
        raise RuntimeError("OpenAI did not return a generated image")

    def _json_response(self, input_payload: list[dict[str, Any]], schema_name: str) -> dict[str, Any]:
        assert self.client is not None
        try:
            response = self.client.responses.create(
                model=self.settings.openai_text_model,
                input=input_payload,
                text={"format": {"type": "json_object"}},
            )
        except TypeError:
            response = self.client.responses.create(
                model=self.settings.openai_text_model,
                input=input_payload,
            )

        text = getattr(response, "output_text", None) or ""
        if not text:
            text_parts: list[str] = []
            for output in getattr(response, "output", []):
                for content in getattr(output, "content", []) or []:
                    if getattr(content, "type", None) in {"output_text", "text"}:
                        text_parts.append(getattr(content, "text", ""))
            text = "\n".join(text_parts)
        return self._parse_json(text, schema_name)

    @staticmethod
    def _parse_json(text: str, schema_name: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                raise ValueError(f"OpenAI response for {schema_name} did not contain JSON")
            return json.loads(match.group(0))


openai_service = OpenAIService()
