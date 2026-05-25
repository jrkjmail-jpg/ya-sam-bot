from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def object_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, это он")],
            [KeyboardButton(text="Нет, другой объект"), KeyboardButton(text="Я не знаю")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
