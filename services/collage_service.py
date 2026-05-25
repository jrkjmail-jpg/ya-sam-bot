from __future__ import annotations

from io import BytesIO
from textwrap import wrap

from PIL import Image, ImageDraw

from services.font_service import load_font
from services.storage_service import storage_service


class CollageService:
    def create_collage(self, title: str, step_images: list[dict]) -> str:
        width, height = 1600, 1900
        collage = Image.new("RGB", (width, height), "#f7f5ff")
        draw = ImageDraw.Draw(collage)
        font_title = load_font(58, bold=True)
        font_logo = load_font(34, bold=True)
        font_caption = load_font(26)
        font_badge = load_font(24, bold=True)

        draw.rounded_rectangle((46, 42, width - 46, 230), radius=34, fill="#ffffff", outline="#eee9fb", width=2)
        draw.ellipse((86, 82, 158, 154), fill="#7c3aed")
        draw.text((122, 118), "Я", fill="#ffffff", font=font_logo, anchor="mm")
        draw.text((188, 78), "\n".join(wrap(title, width=34)[:2]), fill="#161827", font=font_title)
        draw.rounded_rectangle((1220, 72, 1510, 178), radius=24, fill="#f0ebff")
        draw.text((1365, 108), "Пошаговая", fill="#4c1d95", font=font_badge, anchor="mm")
        draw.text((1365, 143), "инструкция", fill="#4c1d95", font=font_caption, anchor="mm")

        cols = 3
        card_w, card_h = 470, 470
        gap_x, gap_y = 42, 52
        start_x, start_y = 46, 280

        for index, item in enumerate(step_images[:6]):
            row = index // cols
            col = index % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=28, fill="#ffffff", outline="#eee9fb", width=2)
            image = self._load_image(item["image_url"])
            image.thumbnail((card_w + 120, card_h + 120))
            paste_x = x + (card_w - image.width) // 2
            paste_y = y + (card_h - image.height) // 2
            collage.paste(image, (paste_x, paste_y))
            draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=28, outline="#eee9fb", width=2)
            draw.ellipse((x + 22, y + 22, x + 76, y + 76), fill="#7c3aed")
            draw.text((x + 49, y + 49), str(item["step_number"]), fill="#ffffff", font=font_badge, anchor="mm")

        info_y = 1350
        draw.rounded_rectangle((46, info_y, 515, 1815), radius=30, fill="#ffffff", outline="#eee9fb", width=2)
        draw.text((86, info_y + 42), "Мои предметы", fill="#161827", font=font_logo)
        draw.text((86, info_y + 88), "Инструкция сохранена", fill="#6b7280", font=font_caption)
        draw.rounded_rectangle((86, info_y + 150, 475, info_y + 255), radius=22, fill="#f7f5ff")
        draw.text((116, info_y + 182), "Открыть инструкцию", fill="#4c1d95", font=font_badge)

        draw.rounded_rectangle((565, info_y, 1034, 1815), radius=30, fill="#ffffff", outline="#eee9fb", width=2)
        draw.text((605, info_y + 42), "Как работает", fill="#161827", font=font_logo)
        for i, line in enumerate(["Понимаю предмет по фото", "Создаю шаги с картинками", "Подстраиваю под ситуацию"]):
            y = info_y + 110 + i * 90
            draw.rounded_rectangle((605, y, 994, y + 64), radius=18, fill="#fbfaff", outline="#eee9fb", width=1)
            draw.ellipse((625, y + 16, 657, y + 48), fill="#ede9fe")
            draw.text((680, y + 19), line, fill="#232333", font=font_caption)

        draw.rounded_rectangle((1084, info_y, 1554, 1815), radius=30, fill="#ffffff", outline="#eee9fb", width=2)
        draw.text((1124, info_y + 42), "Можно спросить", fill="#161827", font=font_logo)
        for i, line in enumerate(["Как открыть?", "Как собрать?", "Как закрепить?", "Как ухаживать?"]):
            x = 1124 + (i % 2) * 205
            y = info_y + 118 + (i // 2) * 145
            draw.rounded_rectangle((x, y, x + 175, y + 105), radius=18, fill="#fbfaff", outline="#eee9fb", width=1)
            draw.text((x + 18, y + 34), line, fill="#232333", font=font_caption)

        draw.text((46, height - 42), "Сфоткай — и я покажу, как сделать самому", fill="#6b7280", font=font_caption)

        buffer = BytesIO()
        collage.save(buffer, format="PNG")
        return storage_service.save_bytes(buffer.getvalue(), "collages", ".png")

    @staticmethod
    def _load_image(url: str) -> Image.Image:
        data = storage_service.get_bytes_if_local(url)
        if not data:
            placeholder = Image.new("RGB", (1024, 1024), "#ffffff")
            draw = ImageDraw.Draw(placeholder)
            draw.text((512, 512), "шаг", fill="#7c3aed", anchor="mm")
            return placeholder
        return Image.open(BytesIO(data)).convert("RGB")


collage_service = CollageService()
