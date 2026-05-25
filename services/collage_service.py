from __future__ import annotations

from io import BytesIO
from textwrap import wrap

from PIL import Image, ImageDraw

from services.font_service import load_font
from services.storage_service import storage_service


class CollageService:
    def create_collage(
        self,
        title: str,
        step_images: list[dict],
        instruction_plan: dict | None = None,
        original_image_url: str | None = None,
    ) -> str:
        width, height = 1400, 1000
        collage = Image.new("RGB", (width, height), "#f7f9fc")
        draw = ImageDraw.Draw(collage)

        font_h1 = load_font(34, bold=True)
        font_h2 = load_font(20, bold=True)
        font_body = load_font(15)
        font_small = load_font(12)
        font_badge = load_font(16, bold=True)

        self._draw_chat_mockup(collage, draw, original_image_url, instruction_plan, font_h2, font_body, font_small)
        self._draw_instruction_area(collage, draw, title, step_images, instruction_plan, font_h1, font_h2, font_body, font_small, font_badge)
        self._draw_bottom_blocks(collage, draw, original_image_url, instruction_plan, font_h2, font_body, font_small)

        buffer = BytesIO()
        collage.save(buffer, format="PNG")
        return storage_service.save_bytes(buffer.getvalue(), "collages", ".png")

    def _draw_chat_mockup(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        original_image_url: str | None,
        instruction_plan: dict | None,
        font_h2,
        font_body,
        font_small,
    ) -> None:
        x, y, w, h = 24, 24, 360, 638
        draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill="#ffffff", outline="#e5e7eb", width=2)
        draw.text((x + 72, y + 24), "Я сам", fill="#111827", font=font_h2)
        draw.text((x + 72, y + 50), "бот", fill="#6b7280", font=font_small)
        draw.ellipse((x + 24, y + 22, x + 58, y + 56), fill="#7c3aed")
        draw.text((x + 41, y + 39), "Я", fill="#ffffff", font=font_small, anchor="mm")

        self._bubble(draw, x + 30, y + 95, 230, 94, "Привет!\nЯ помогу разобраться\nс вашим предметом.", font_body)
        self._draw_reference_tile(draw, x + 74, y + 215, 252, 220, instruction_plan, font_small)

        self._bubble(draw, x + 86, y + 472, 240, 50, "Как сделать самому?", font_body, outgoing=True)
        detected = (instruction_plan or {}).get("title") or "Инструкция готова"
        self._bubble(draw, x + 30, y + 548, 276, 72, f"Готово.\n{detected[:42]}", font_body)

    def _draw_instruction_area(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        title: str,
        step_images: list[dict],
        instruction_plan: dict | None,
        font_h1,
        font_h2,
        font_body,
        font_small,
        font_badge,
    ) -> None:
        x, y, w, h = 408, 24, 968, 638
        draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill="#ffffff", outline="#e5e7eb", width=2)
        draw.ellipse((x + 26, y + 26, x + 70, y + 70), fill="#7c3aed")
        draw.text((x + 48, y + 48), "i", fill="#ffffff", font=font_badge, anchor="mm")
        draw.text((x + 88, y + 24), "\n".join(wrap(title, width=34)[:2]), fill="#111827", font=font_h1)
        draw.text((x + 88, y + 98), "Пошаговая инструкция", fill="#6b7280", font=font_body)

        suitable_for = (instruction_plan or {}).get("suitable_for") or "Под ваш предмет и ситуацию"
        draw.rounded_rectangle((x + 704, y + 24, x + 938, y + 112), radius=18, fill="#f3f0ff")
        for i, line in enumerate(wrap(suitable_for, width=25)[:3]):
            draw.text((x + 724, y + 40 + i * 20), line, fill="#4c1d95", font=font_small)

        steps = (instruction_plan or {}).get("steps", [])
        card_w, card_h = 292, 228
        gap = 20
        start_x, start_y = x + 26, y + 150
        for index, item in enumerate(step_images[:6]):
            row, col = divmod(index, 3)
            cx = start_x + col * (card_w + gap)
            cy = start_y + row * (card_h + gap)
            step = steps[index] if index < len(steps) else {}
            self._draw_step_card(canvas, draw, cx, cy, card_w, card_h, item, step, font_h2, font_body, font_small)

    def _draw_step_card(self, canvas, draw, x, y, w, h, item, step, font_h2, font_body, font_small) -> None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill="#ffffff", outline="#e5e7eb", width=2)
        draw.ellipse((x + 16, y + 14, x + 42, y + 40), fill="#7c3aed")
        draw.text((x + 29, y + 27), str(item.get("step_number", "")), fill="#ffffff", font=font_small, anchor="mm")
        draw.text((x + 54, y + 15), (step.get("title") or f"Шаг {item.get('step_number')}")[:22], fill="#111827", font=font_h2)

        image = self._load_image(item["image_url"])
        draw.rounded_rectangle((x + 14, y + 50, x + w - 14, y + 174), radius=16, fill="#f8fafc")
        if image:
            image = self._extract_step_visual(image)
            image.thumbnail((w - 28, 118))
            ix = x + (w - image.width) // 2
            iy = y + 54
            canvas.paste(image, (ix, iy))

        description = step.get("description") or ""
        text_y = y + 178
        for line in wrap(description, width=38)[:2]:
            draw.text((x + 18, text_y), line, fill="#374151", font=font_small)
            text_y += 16

    def _draw_bottom_blocks(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        original_image_url: str | None,
        instruction_plan: dict | None,
        font_h2,
        font_body,
        font_small,
    ) -> None:
        y = 690
        blocks = [(24, 360), (408, 430), (862, 514)]
        for x, w in blocks:
            draw.rounded_rectangle((x, y, x + w, 966), radius=26, fill="#ffffff", outline="#e5e7eb", width=2)

        draw.text((54, y + 30), "Мои предметы", fill="#111827", font=font_h2)
        draw.text((54, y + 58), "Ваши сохраненные инструкции", fill="#6b7280", font=font_small)
        self._draw_reference_tile(draw, 54, y + 94, 84, 84, instruction_plan, font_small)
        draw.text((154, y + 104), ((instruction_plan or {}).get("title") or "Новая инструкция")[:25], fill="#111827", font=font_body)
        draw.rounded_rectangle((154, y + 152, 330, y + 194), radius=16, fill="#7c3aed")
        draw.text((242, y + 173), "Открыть инструкцию", fill="#ffffff", font=font_small, anchor="mm")

        draw.text((438, y + 30), "Как работает «Я сам»", fill="#111827", font=font_h2)
        for i, text in enumerate(["Понимает предмет по фото", "Создает шаги с картинками", "Адаптирует под ситуацию", "Показывает понятный результат"]):
            yy = y + 78 + i * 45
            draw.rounded_rectangle((438, yy, 804, yy + 34), radius=14, fill="#f8fafc", outline="#eef2ff")
            draw.ellipse((456, yy + 8, 474, yy + 26), fill="#ddd6fe")
            draw.text((492, yy + 8), text, fill="#374151", font=font_small)

        draw.text((892, y + 30), "Примеры того, что можно спросить", fill="#111827", font=font_h2)
        examples = ["Как открыть бутылку?", "Как надеть кепку?", "Как сложить палатку?", "Как установить кресло?", "Как пользоваться кофемашиной?", "Как собрать стул?"]
        for i, text in enumerate(examples):
            col, row = i % 3, i // 3
            xx = 892 + col * 154
            yy = y + 82 + row * 102
            draw.rounded_rectangle((xx, yy, xx + 132, yy + 82), radius=16, fill="#f8fafc", outline="#e5e7eb")
            for j, line in enumerate(wrap(text, width=15)[:2]):
                draw.text((xx + 10, yy + 44 + j * 15), line, fill="#111827", font=font_small)

    @staticmethod
    def _bubble(draw, x, y, w, h, text, font, outgoing: bool = False) -> None:
        fill = "#dbeafe" if outgoing else "#ffffff"
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline="#e5e7eb")
        for i, line in enumerate(text.splitlines()):
            draw.text((x + 16, y + 14 + i * 20), line, fill="#111827", font=font)

    @staticmethod
    def _load_image(url: str | None) -> Image.Image | None:
        if not url:
            return None
        data = storage_service.get_bytes_if_local(url)
        if not data:
            return None
        return Image.open(BytesIO(data)).convert("RGB")

    @staticmethod
    def _draw_reference_tile(
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        w: int,
        h: int,
        instruction_plan: dict | None,
        font_small,
    ) -> None:
        reference = ((instruction_plan or {}).get("object_reference") or {}).get("visual_reference_prompt")
        name = (instruction_plan or {}).get("instruction_target") or ((instruction_plan or {}).get("title") or "предмет")
        draw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill="#f8fafc", outline="#e5e7eb", width=2)
        cx, cy = x + w // 2, y + h // 2 - 12
        body_w = min(140, max(50, w - 64))
        body_h = min(78, max(36, h - 44))
        side = max(14, min(42, w // 6))
        stroke = 4 if w >= 150 else 2
        draw.rounded_rectangle(
            (cx - body_w // 2, cy - body_h // 2, cx + body_w // 2, cy + body_h // 2),
            radius=max(16, body_h // 2),
            fill="#ffffff",
            outline="#c4b5fd",
            width=stroke,
        )
        draw.ellipse((x + 12, cy - side // 2, x + 12 + side, cy + side // 2), fill="#ede9fe", outline="#7c3aed", width=stroke)
        draw.ellipse((x + w - 12 - side, cy - side // 2, x + w - 12, cy + side // 2), fill="#dff7ff", outline="#38bdf8", width=stroke)
        label = reference or name
        text_y = y + h - 45
        for line in wrap(label, width=max(12, w // 11))[:2]:
            draw.text((x + 12, text_y), line, fill="#6b7280", font=font_small)
            text_y += 15

    @staticmethod
    def _extract_step_visual(image: Image.Image) -> Image.Image:
        if image.width == image.height and image.width >= 900:
            return image.crop((96, 230, 928, 690))
        return image


collage_service = CollageService()
