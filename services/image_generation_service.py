from __future__ import annotations

from io import BytesIO
import logging
from textwrap import wrap

from PIL import Image, ImageDraw

from config.settings import get_settings
from services.openai_service import openai_service
from services.font_service import load_font
from services.storage_service import storage_service


logger = logging.getLogger(__name__)


class ImageGenerationService:
    def generate_step_images(self, source_image_url: str, steps: list[dict]) -> list[dict]:
        settings = get_settings()
        results: list[dict] = []
        for index, step in enumerate(steps, start=1):
            should_use_ai_image = (
                settings.enable_ai_step_images
                and not settings.ai_is_mocked
                and index <= max(0, settings.max_ai_step_images)
            )
            if not should_use_ai_image:
                image_bytes = self._placeholder_card(step)
            else:
                try:
                    image_bytes = openai_service.generate_step_image(
                        source_image_url,
                        self._step_image_prompt(step),
                    )
                except Exception:
                    logger.exception(
                        "OpenAI image generation failed for step %s; using fallback card",
                        step.get("step_number"),
                    )
                    image_bytes = self._placeholder_card(step)
            image_url = storage_service.save_bytes(image_bytes, "generated", ".png")
            results.append({"step_number": step["step_number"], "image_url": image_url})
        return results

    @staticmethod
    def _step_image_prompt(step: dict) -> str:
        visual_spec = step.get("visual_spec") or {}
        return "\n".join(
            [
                step.get("image_prompt") or step.get("visual_prompt") or "",
                f"Цель шага: {step.get('title')} — {step.get('description')}",
                f"Тип действия: {step.get('action_type')}",
                f"Фокус: {step.get('focus_area')}",
                f"Ракурс: {step.get('camera_angle')}",
                f"Рука/палец: {step.get('hand_action')}",
                f"Подсветка: {step.get('visual_highlight')}",
                f"До: {step.get('state_before')}",
                f"После: {step.get('state_after')}",
                f"Объект: {visual_spec.get('main_object')}",
                f"Сцена: {visual_spec.get('scene')}",
                f"Композиция: {visual_spec.get('composition')}",
                f"Обязательно сохранить: {', '.join(visual_spec.get('required_elements', []))}",
                f"Избегать: {', '.join(visual_spec.get('avoid', []))}",
            ]
        )

    @staticmethod
    def _placeholder_card(step: dict) -> bytes:
        width, height = 1024, 1024
        image = Image.new("RGB", (width, height), "#f7f5ff")
        draw = ImageDraw.Draw(image)
        font_title = load_font(50, bold=True)
        font_body = load_font(28)
        font_small = load_font(22)
        font_brand = load_font(26, bold=True)

        draw.rounded_rectangle((46, 46, 978, 978), radius=38, fill="#ffffff", outline="#ebe7f7", width=3)
        draw.ellipse((76, 76, 148, 148), fill="#7c3aed")
        draw.text((112, 112), str(step["step_number"]), fill="#ffffff", font=font_brand, anchor="mm")
        draw.text((174, 78), "Я сам", fill="#7c3aed", font=font_small)
        draw.text((174, 116), step["title"][:34], fill="#161827", font=font_title)

        object_box = (96, 230, 928, 682)
        draw.rounded_rectangle(object_box, radius=34, fill="#fbfbff", outline="#efeafb", width=2)

        ImageGenerationService._draw_object_model(draw, step, object_box)

        ImageGenerationService._draw_instruction_marks(draw, step.get("step_number", 1))

        draw.rounded_rectangle((96, 724, 928, 922), radius=24, fill="#faf9ff", outline="#eee9fb", width=2)
        y = 752
        for line in wrap(step["description"], width=50)[:5]:
            draw.text((126, y), line, fill="#232333", font=font_body)
            y += 38

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _draw_instruction_marks(draw: ImageDraw.ImageDraw, step_number: int) -> None:
        purple = "#8b5cf6"
        violet = "#6d28d9"
        blue = "#38bdf8"
        orange = "#fb923c"

        if step_number % 3 == 1:
            draw.arc((350, 300, 710, 620), start=25, end=330, fill=purple, width=10)
            draw.polygon([(700, 374), (762, 355), (726, 410)], fill=purple)
            for x, y in [(770, 270), (810, 300), (790, 345)]:
                draw.line((x, y, x + 38, y - 24), fill=violet, width=7)
        elif step_number % 3 == 2:
            draw.line((235, 560, 760, 560), fill=orange, width=12)
            draw.polygon([(760, 520), (838, 560), (760, 600)], fill=orange)
            draw.ellipse((407, 430, 617, 640), outline=blue, width=8)
            for y in (358, 394, 430):
                draw.arc((735, y, 860, y + 115), start=300, end=60, fill=purple, width=8)
        else:
            draw.ellipse((305, 298, 715, 650), outline=purple, width=10)
            draw.line((690, 330, 820, 250), fill=purple, width=10)
            draw.polygon([(820, 250), (790, 312), (754, 258)], fill=purple)
            for x in (210, 250, 290):
                draw.line((x, 300, x - 34, 260), fill=violet, width=7)

    @staticmethod
    def _draw_object_model(draw: ImageDraw.ImageDraw, step: dict, object_box: tuple[int, int, int, int]) -> None:
        visual_spec = step.get("visual_spec") or {}
        object_text = visual_spec.get("main_object") or "визуальная модель объекта"
        font_small = load_font(22)

        draw.rounded_rectangle((230, 315, 794, 590), radius=42, fill="#f0eef8", outline="#ddd6fe", width=2)
        draw.rounded_rectangle((325, 370, 700, 540), radius=70, fill="#ffffff", outline="#c4b5fd", width=5)
        draw.ellipse((272, 388, 360, 476), fill="#ede9fe", outline="#7c3aed", width=4)
        draw.ellipse((666, 388, 754, 476), fill="#dff7ff", outline="#38bdf8", width=4)
        draw.rounded_rectangle((435, 300, 590, 370), radius=36, fill="#dff7ff", outline="#38bdf8", width=4)

        y = object_box[3] - 70
        for line in wrap(object_text, width=48)[:2]:
            draw.text((512, y), line, fill="#6b5f90", font=font_small, anchor="mm")
            y += 28


image_generation_service = ImageGenerationService()
