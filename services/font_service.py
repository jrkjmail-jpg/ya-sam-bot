from __future__ import annotations

from pathlib import Path

from PIL import ImageFont


FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
)


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = list(FONT_CANDIDATES)
    if bold:
        candidates.insert(0, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)

    return ImageFont.load_default(size=size)
