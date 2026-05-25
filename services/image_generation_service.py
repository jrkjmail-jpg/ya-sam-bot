from __future__ import annotations

from io import BytesIO
import logging
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from config.settings import get_settings
from services.openai_service import openai_service
from services.font_service import load_font
from services.storage_service import storage_service


logger = logging.getLogger(__name__)


class ImageGenerationService:
    def generate_step_images(self, source_image_url: str, steps: list[dict]) -> list[dict]:
        settings = get_settings()
        results: list[dict] = []
        for step in steps:
            if settings.ai_is_mocked:
                image_bytes = self._placeholder_card(step, source_image_url)
            else:
                try:
                    image_bytes = openai_service.generate_step_image(source_image_url, step["visual_prompt"])
                except Exception:
                    logger.exception(
                        "OpenAI image generation failed for step %s; using fallback card",
                        step.get("step_number"),
                    )
                    image_bytes = self._placeholder_card(step, source_image_url)
            image_url = storage_service.save_bytes(image_bytes, "generated", ".png")
            results.append({"step_number": step["step_number"], "image_url": image_url})
        return results

    @staticmethod
    def _placeholder_card(step: dict, source_image_url: str | None = None) -> bytes:
        width, height = 1024, 1024
        image = Image.new("RGB", (width, height), "#101216")
        draw = ImageDraw.Draw(image)
        font_title = load_font(52, bold=True)
        font_body = load_font(32)
        font_small = load_font(24)

        draw.rounded_rectangle((56, 56, 968, 968), radius=36, fill="#1b2028", outline="#2dd4ff", width=3)
        draw.ellipse((78, 78, 170, 170), fill="#ff8a1f")
        draw.text((112, 103), str(step["step_number"]), fill="#ffffff", font=font_title, anchor="mm")
        draw.text((205, 86), "Я сам", fill="#7de7ff", font=font_small)
        draw.text((205, 124), step["title"], fill="#ffffff", font=font_title)

        object_box = (170, 285, 854, 660)
        draw.rounded_rectangle(object_box, radius=32, fill="#262d38", outline="#364150", width=2)

        source_image = ImageGenerationService._load_source_preview(source_image_url)
        if source_image:
            source_image.thumbnail((640, 330))
            paste_x = 512 - source_image.width // 2
            paste_y = 472 - source_image.height // 2
            image.paste(source_image, (paste_x, paste_y))
            draw.rounded_rectangle(object_box, radius=32, outline="#364150", width=2)

        draw.line((270, 510, 720, 510), fill="#ff8a1f", width=14)
        draw.polygon([(720, 472), (805, 510), (720, 548)], fill="#ff8a1f")
        draw.ellipse((410, 395, 615, 600), outline="#2dd4ff", width=8)
        draw.text((512, 690), "важная зона выделена", fill="#b8c4d6", font=font_small, anchor="mm")

        y = 780
        for line in wrap(step["description"], width=43)[:4]:
            draw.text((96, y), line, fill="#e8edf5", font=font_body)
            y += 44

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _load_source_preview(source_image_url: str | None) -> Image.Image | None:
        if not source_image_url:
            return None
        data = storage_service.get_bytes_if_local(source_image_url)
        if not data:
            return None
        try:
            return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            logger.exception("Could not load source image preview for fallback card")
            return None


image_generation_service = ImageGenerationService()
