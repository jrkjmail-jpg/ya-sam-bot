from __future__ import annotations

import hashlib


ACTION_VERBS = (
    "прикреп",
    "наж",
    "повер",
    "проверь",
    "проверьте",
    "протр",
    "постав",
    "встав",
    "закреп",
    "открой",
    "закрой",
    "подключ",
    "надень",
    "сними",
    "покаж",
    "использ",
)


class QualityService:
    def check_plan(self, instruction: dict) -> dict:
        problems: list[str] = []
        steps_to_regenerate: list[int] = []
        seen_prompts: set[str] = set()

        for step in instruction.get("steps", []):
            number = step.get("step_number")
            text = f"{step.get('title', '')} {step.get('description', '')}".lower()
            has_action = any(verb in text for verb in ACTION_VERBS) or bool(step.get("action_type"))
            if not has_action:
                problems.append(f"Шаг {number}: нет конкретного действия")
                steps_to_regenerate.append(number)
            if not step.get("focus_area"):
                problems.append(f"Шаг {number}: нет focus_area")
                steps_to_regenerate.append(number)
            if not step.get("image_prompt") and not step.get("visual_prompt"):
                problems.append(f"Шаг {number}: нет image_prompt")
                steps_to_regenerate.append(number)

            prompt_hash = hashlib.sha1((step.get("image_prompt") or step.get("visual_prompt") or "").encode()).hexdigest()
            if prompt_hash in seen_prompts:
                problems.append(f"Шаг {number}: повторяется визуальный промпт")
                steps_to_regenerate.append(number)
            seen_prompts.add(prompt_hash)

        return {
            "is_good": not problems,
            "problems": problems,
            "steps_to_regenerate": sorted(set(filter(None, steps_to_regenerate))),
        }


quality_service = QualityService()
