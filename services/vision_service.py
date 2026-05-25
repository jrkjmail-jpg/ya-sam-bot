from __future__ import annotations

from config.settings import get_settings
from services.openai_service import openai_service
from services.safety import looks_potentially_dangerous


class VisionService:
    def identify(self, image_urls: list[str]) -> dict:
        return self.analyze(
            image_urls,
            "Определи главный объект, для которого пользователь хочет получить инструкцию. Пользователь еще не написал действие.",
        )

    def analyze(self, image_url: str | list[str], user_goal: str) -> dict:
        settings = get_settings()
        if looks_potentially_dangerous(user_goal):
            return {
                "detected_object": "объект с потенциальным риском",
                "user_goal": user_goal,
                "confidence": 0.7,
                "important_visible_parts": [],
                "missing_information": ["безопасный способ выполнения"],
                "needs_clarification": True,
                "clarification_question": "Похоже, здесь может быть риск. Я могу помочь только с безопасным бытовым вариантом или подсказать, когда лучше обратиться к специалисту.",
                "can_generate_instruction": False,
            }
        if settings.ai_is_mocked:
            return self._mock_analysis(user_goal)
        return openai_service.analyze_object(image_url, user_goal)

    @staticmethod
    def _mock_analysis(user_goal: str) -> dict:
        lowered = user_goal.lower()
        if any(word in lowered for word in ("модель", "подключ", "настро", "кноп")):
            return {
                "detected_object": "предмет с кнопками или креплениями",
                "user_goal": user_goal,
                "confidence": 0.74,
                "important_visible_parts": ["передняя часть", "основные элементы"],
                "missing_information": ["боковая сторона", "маркировка или модель"],
                "needs_clarification": True,
                "clarification_question": "Чтобы показать точнее, пришлите фото сбоку или напишите модель, если знаете.",
                "can_generate_instruction": False,
            }

        return {
            "detected_object": "предмет на фото",
            "user_goal": user_goal,
            "confidence": 0.86,
            "important_visible_parts": ["основная форма", "видимые крепления", "рабочая зона"],
            "missing_information": [],
            "needs_clarification": False,
            "clarification_question": None,
            "can_generate_instruction": True,
        }


vision_service = VisionService()
