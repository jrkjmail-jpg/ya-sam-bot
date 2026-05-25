from __future__ import annotations

from io import BytesIO
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from services.font_service import load_font
from services.storage_service import storage_service


class CollageService:
    def create_collage(self, title: str, step_images: list[dict]) -> str:
        width, height = 1400, 1800
        collage = Image.new("RGB", (width, height), "#0d0f13")
        draw = ImageDraw.Draw(collage)
        font_title = load_font(66, bold=True)
        font_logo = load_font(34, bold=True)
        font_caption = load_font(28)

        draw.text((70, 55), "Я сам", fill="#7de7ff", font=font_logo)
        draw.text((70, 105), "\n".join(wrap(title, width=28)[:2]), fill="#ffffff", font=font_title)
        draw.rounded_rectangle((1010, 62, 1320, 148), radius=28, fill="#1b2028", outline="#ff8a1f", width=2)
        draw.text((1165, 105), "пошагово", fill="#ffffff", font=font_caption, anchor="mm")

        cols = 2
        card_w, card_h = 590, 590
        gap_x, gap_y = 70, 80
        start_x, start_y = 70, 275

        for index, item in enumerate(step_images[:6]):
            row = index // cols
            col = index % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            draw.rounded_rectangle((x - 8, y - 8, x + card_w + 8, y + card_h + 8), radius=34, fill="#181d25")
            image = self._load_image(item["image_url"])
            image.thumbnail((card_w, card_h))
            paste_x = x + (card_w - image.width) // 2
            paste_y = y + (card_h - image.height) // 2
            collage.paste(image, (paste_x, paste_y))
            draw.ellipse((x + 22, y + 22, x + 88, y + 88), fill="#ff8a1f")
            draw.text((x + 55, y + 55), str(item["step_number"]), fill="#ffffff", font=font_caption, anchor="mm")

        footer_y = height - 105
        draw.line((70, footer_y - 28, width - 70, footer_y - 28), fill="#27313d", width=2)
        draw.text((70, footer_y), "Сфоткай — и я покажу, как сделать самому", fill="#b8c4d6", font=font_caption)

        buffer = BytesIO()
        collage.save(buffer, format="PNG")
        return storage_service.save_bytes(buffer.getvalue(), "collages", ".png")

    @staticmethod
    def _load_image(url: str) -> Image.Image:
        data = storage_service.get_bytes_if_local(url)
        if not data:
            placeholder = Image.new("RGB", (1024, 1024), "#1b2028")
            draw = ImageDraw.Draw(placeholder)
            draw.text((512, 512), "step", fill="#ffffff", anchor="mm")
            return placeholder
        return Image.open(BytesIO(data)).convert("RGB")


collage_service = CollageService()
