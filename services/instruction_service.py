from __future__ import annotations

from config.settings import get_settings
from services.openai_service import openai_service
from services.quality_service import quality_service
from services.safety import looks_potentially_dangerous


class InstructionService:
    def generate(self, image_url: str, user_goal: str, confirmed_details: str | None = None) -> dict:
        settings = get_settings()
        if looks_potentially_dangerous(f"{user_goal} {confirmed_details or ''}"):
            return self._normalize_instruction(self._safe_alternative(user_goal), user_goal)
        if settings.ai_is_mocked:
            return self._normalize_instruction(self._mock_instruction(user_goal), user_goal)

        instruction = openai_service.generate_instruction(image_url, user_goal, confirmed_details)
        instruction = self._normalize_instruction(instruction, user_goal)
        return instruction

    def _normalize_instruction(self, instruction: dict, user_goal: str) -> dict:
        instruction.setdefault("title", "Как сделать самому")
        instruction.setdefault("short_summary", f"Пошаговая инструкция для задачи: {user_goal}.")
        instruction.setdefault("suitable_for", "Для бытового безопасного использования")
        instruction.setdefault("safety_notes", [])
        instruction.setdefault("extra_sections", [])
        steps = instruction.get("steps", [])[:6]
        normalized_steps = []
        for index, step in enumerate(steps, start=1):
            step.setdefault("step_number", index)
            step.setdefault("title", f"Шаг {index}")
            step.setdefault("description", "Выполните действие аккуратно и проверьте результат.")
            step.setdefault("action_type", "use")
            step.setdefault("focus_area", "важная часть объекта")
            step.setdefault("camera_angle", "крупный план")
            step.setdefault("hand_action", "рука показывает действие")
            step.setdefault("visual_highlight", "фиолетовая стрелка и круг выделяют важную часть")
            step.setdefault("state_before", "до действия")
            step.setdefault("state_after", "после действия")
            step.setdefault(
                "visual_spec",
                {
                    "main_object": "объект с исходного фото",
                    "scene": "чистый фон",
                    "composition": step["camera_angle"],
                    "required_elements": ["объект похож на исходное фото"],
                    "action": step["description"],
                    "highlight": step["visual_highlight"],
                    "avoid": ["не менять объект", "не добавлять лишние элементы"],
                },
            )
            step.setdefault("image_prompt", self._build_image_prompt(step))
            step.setdefault("visual_prompt", step["image_prompt"])
            normalized_steps.append(step)
        instruction["steps"] = normalized_steps
        instruction["quality_check"] = quality_service.check_plan(instruction)
        return instruction

    @staticmethod
    def _build_image_prompt(step: dict) -> str:
        visual_spec = step.get("visual_spec") or {}
        return (
            f"Шаг {step.get('step_number')}: {step.get('title')}. "
            f"Действие: {step.get('description')}. "
            f"Фокус: {step.get('focus_area')}. "
            f"Ракурс: {step.get('camera_angle')}. "
            f"Действие рукой: {step.get('hand_action')}. "
            f"Подсветка: {step.get('visual_highlight')}. "
            f"До: {step.get('state_before')}. После: {step.get('state_after')}. "
            f"Сохранить: {', '.join(visual_spec.get('required_elements', []))}."
        )

    @staticmethod
    def _mock_instruction(user_goal: str) -> dict:
        return {
            "title": "Как сделать самому",
            "short_summary": f"Простая инструкция для задачи: {user_goal}.",
            "suitable_for": "Для безопасного бытового действия",
            "safety_notes": ["Делайте шаги спокойно и остановитесь, если предмет выглядит поврежденным."],
            "steps": [
                {
                    "step_number": 1,
                    "title": "Осмотрите предмет",
                    "description": "Поверните предмет к себе основной стороной и найдите важные элементы.",
                    "visual_prompt": "Предмет крупно по центру, подсвечены основные видимые элементы.",
                },
                {
                    "step_number": 2,
                    "title": "Подготовьте место",
                    "description": "Положите предмет на устойчивую поверхность, чтобы он не скользил.",
                    "visual_prompt": "Предмет на темной поверхности, вокруг свободное место, мягкая голубая подсветка.",
                },
                {
                    "step_number": 3,
                    "title": "Сделайте главное действие",
                    "description": "Выполните действие медленно, без усилия. Если что-то не идет, не давите.",
                    "visual_prompt": "Оранжевая стрелка показывает направление основного действия.",
                },
                {
                    "step_number": 4,
                    "title": "Проверьте результат",
                    "description": "Убедитесь, что предмет стоит ровно, держится надежно или работает как нужно.",
                    "visual_prompt": "Готовый результат, зеленовато-голубая отметка, аккуратный финальный вид.",
                },
            ],
            "extra_sections": [],
        }

    @staticmethod
    def _safe_alternative(user_goal: str) -> dict:
        return {
            "title": "Безопасный вариант",
            "short_summary": f"В задаче «{user_goal}» есть риск, поэтому я не буду давать опасные пошаговые действия.",
            "suitable_for": "Для безопасной остановки действия",
            "safety_notes": ["Не разбирайте опасные элементы самостоятельно.", "Остановитесь и обратитесь к специалисту."],
            "steps": [
                {
                    "step_number": 1,
                    "title": "Остановитесь",
                    "description": "Не продолжайте действие, если есть риск травмы, электричества, газа, оружия или химикатов.",
                    "visual_prompt": "Темная карточка безопасности с оранжевым предупреждающим маркером.",
                },
                {
                    "step_number": 2,
                    "title": "Уберите риск",
                    "description": "Отойдите от предмета, не трогайте опасные части и ограничьте доступ детям.",
                    "visual_prompt": "Предмет на безопасном расстоянии, зона риска отмечена оранжевым кругом.",
                },
                {
                    "step_number": 3,
                    "title": "Позовите помощь",
                    "description": "Для таких задач лучше вызвать профильного специалиста или службу поддержки.",
                    "visual_prompt": "Телефон и спокойная подсказка обратиться за помощью.",
                },
            ],
            "extra_sections": [],
        }


instruction_service = InstructionService()
