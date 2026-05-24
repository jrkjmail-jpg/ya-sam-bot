from __future__ import annotations

from config.settings import get_settings
from services.openai_service import openai_service
from services.safety import looks_potentially_dangerous


class InstructionService:
    def generate(self, image_url: str, user_goal: str, confirmed_details: str | None = None) -> dict:
        settings = get_settings()
        if looks_potentially_dangerous(f"{user_goal} {confirmed_details or ''}"):
            return self._safe_alternative(user_goal)
        if settings.ai_is_mocked:
            return self._mock_instruction(user_goal)

        instruction = openai_service.generate_instruction(image_url, user_goal, confirmed_details)
        instruction["steps"] = instruction.get("steps", [])[:7]
        return instruction

    @staticmethod
    def _mock_instruction(user_goal: str) -> dict:
        return {
            "title": "Как сделать самому",
            "short_summary": f"Простая инструкция для задачи: {user_goal}.",
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
        }

    @staticmethod
    def _safe_alternative(user_goal: str) -> dict:
        return {
            "title": "Безопасный вариант",
            "short_summary": f"В задаче «{user_goal}» есть риск, поэтому я не буду давать опасные пошаговые действия.",
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
        }


instruction_service = InstructionService()
