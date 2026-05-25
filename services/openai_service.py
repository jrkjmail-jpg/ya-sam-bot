from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from config.settings import BASE_DIR, get_settings
from services.storage_service import storage_service


logger = logging.getLogger(__name__)


class OpenAIQuotaError(RuntimeError):
    pass


def _read_prompt(name: str) -> str:
    return (BASE_DIR / "prompts" / name).read_text(encoding="utf-8")


def _is_insufficient_quota(error: Exception) -> bool:
    return "insufficient_quota" in str(error) or "exceeded your current quota" in str(error).lower()


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

    def analyze_object(self, image_url: str | list[str], user_goal: str) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        prompt = _read_prompt("analyze_object_prompt.txt")
        image_urls = image_url if isinstance(image_url, list) else [image_url]
        content = [{"type": "input_text", "text": f"{prompt}\n\nЦель пользователя: {user_goal}"}]
        content.extend({"type": "input_image", "image_url": self._image_input(url)} for url in image_urls)
        input_payload = [
            {
                "role": "user",
                "content": content,
            }
        ]
        return self._json_response(input_payload, "yasam_object_analysis", use_web_search=True)

    def generate_instruction(
        self,
        image_url: str,
        user_goal: str,
        confirmed_details: str | None,
        analysis: dict | None = None,
    ) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        prompt = _read_prompt("generate_instruction_prompt.txt")
        details = confirmed_details or "Дополнительных уточнений нет."
        analysis_text = json.dumps(analysis or {}, ensure_ascii=False)
        input_payload = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"{prompt}\n\n"
                            f"Цель пользователя: {user_goal}\n"
                            f"Подтверждение/уточнения: {details}\n"
                            f"Глубокий анализ объекта и найденной информации: {analysis_text}"
                        ),
                    }
                ],
            }
        ]
        return self._json_response(input_payload, "yasam_instruction")

    def generate_step_image(self, source_image_url: str, visual_prompt: str) -> bytes:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        style = f"{_read_prompt('image_prompt_style.txt')}\n\n{_read_prompt('step_image_prompt.txt')}"
        image_tool = {
            "type": "image_generation",
            "action": "auto",
            "model": self.settings.openai_image_model,
            "size": "1024x1024",
            "quality": "high",
        }

        try:
            response = self.client.responses.create(
                model=self.settings.openai_text_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": f"{style}\n\nСцена шага: {visual_prompt}"},
                        ],
                    }
                ],
                tools=[image_tool],
            )
        except Exception as exc:
            if _is_insufficient_quota(exc):
                raise OpenAIQuotaError("OpenAI API quota is insufficient") from exc
            raise
        for output in response.output:
            if getattr(output, "type", None) == "image_generation_call" and getattr(output, "result", None):
                return base64.b64decode(output.result)
        raise RuntimeError("OpenAI did not return a generated image")

    def _json_response(
        self,
        input_payload: list[dict[str, Any]],
        schema_name: str,
        use_web_search: bool = False,
    ) -> dict[str, Any]:
        assert self.client is not None
        try:
            request: dict[str, Any] = {
                "model": self.settings.openai_text_model,
                "input": input_payload,
                "text": {"format": {"type": "json_object"}},
            }
            if use_web_search:
                request["tools"] = [{"type": "web_search"}]
                request["tool_choice"] = "auto"
            response = self.client.responses.create(**request)
        except TypeError:
            response = self.client.responses.create(
                model=self.settings.openai_text_model,
                input=input_payload,
            )
        except Exception as exc:
            if _is_insufficient_quota(exc):
                raise OpenAIQuotaError("OpenAI API quota is insufficient") from exc
            if not use_web_search:
                raise
            logger.exception("OpenAI web search analysis failed; retrying without web search")
            try:
                response = self.client.responses.create(
                    model=self.settings.openai_text_model,
                    input=input_payload,
                    text={"format": {"type": "json_object"}},
                )
            except Exception as retry_exc:
                if _is_insufficient_quota(retry_exc):
                    raise OpenAIQuotaError("OpenAI API quota is insufficient") from retry_exc
                raise

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
