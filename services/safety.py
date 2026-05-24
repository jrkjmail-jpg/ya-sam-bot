from __future__ import annotations


DANGEROUS_KEYWORDS = (
    "оруж",
    "пистолет",
    "винтов",
    "ножев",
    "патрон",
    "взрыв",
    "электрощит",
    "проводка",
    "220",
    "розетку чин",
    "газ",
    "кислот",
    "щелоч",
    "лекар",
    "укол",
    "операц",
    "медицин",
)


def looks_potentially_dangerous(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DANGEROUS_KEYWORDS)
