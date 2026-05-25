# Я сам

MVP Telegram-бота: пользователь присылает фото и пишет, что хочет сделать, а бот создает простую визуальную инструкцию по шагам.

## Что внутри

- `bot/` — Telegram-бот на aiogram 3.
- `api/` — FastAPI backend.
- `services/` — AI-анализ, генерация инструкций, изображений, коллажа и storage.
- `database/` — SQLAlchemy-модели и репозитории.
- `prompts/` — промпты анализа, инструкции и визуального стиля.
- `storage/` — локальное хранилище фото, карточек и коллажей для разработки.

## Установка локально

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`:

```env
TELEGRAM_BOT_TOKEN=токен_бота
# Если хостинг сам передает токен как BOT_TOKEN, можно заполнить BOT_TOKEN вместо TELEGRAM_BOT_TOKEN.
BOT_TOKEN=
OPENAI_API_KEY=ключ_openai
DATABASE_URL=sqlite:///./yasam.db
API_BASE_URL=http://localhost:8000
```

Если хостинг задает переменную `PORT`, бот автоматически использует этот порт для локальной связи с API.

Для локального теста без OpenAI можно поставить:

```env
USE_MOCK_AI=true
```

Тогда бот пройдет полный сценарий с тестовыми шагами и сгенерирует placeholder-карточки.

## Запуск FastAPI

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Проверка:

```bash
curl http://localhost:8000/health
```

Документация API:

```text
http://localhost:8000/docs
```

## Запуск Telegram-бота

В отдельном терминале:

```bash
source .venv/bin/activate
python -m bot.main
```

## Запуск одним процессом

Для простого бот-хостинга можно поднять API и бота вместе:

```bash
python -m scripts.run_all
```

Подробная инструкция по размещению: [DEPLOYMENT.md](DEPLOYMENT.md).

## Запуск через Docker

```bash
cp .env.example .env
docker compose up --build
```

В Docker используется PostgreSQL. Таблицы создаются автоматически при старте API.

## OpenAI API

Нужен `OPENAI_API_KEY`.

Используются:

- vision-анализ фото через Responses API;
- генерация строгого JSON для анализа и инструкции;
- генерация визуальных карточек через image generation tool.

Если фото лежит в локальном `storage/`, backend передает его в модель как base64 data URL. Если используется Supabase Storage с публичными URL, модель получает URL.

## Supabase

Для Supabase заполните:

```env
DATABASE_URL=postgresql+psycopg://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
STORAGE_BUCKET=yasam
```

Если нужно именно Supabase Storage, поставьте дополнительный пакет:

```bash
pip install -r requirements-supabase.txt
```

Если Supabase-переменные пустые, файлы сохраняются локально в `storage/`.

## Полный сценарий тестирования

1. Запустите API.
2. Запустите Telegram-бота.
3. Отправьте `/start`.
4. Пришлите фото предмета.
5. Если у вас несколько ракурсов, отправьте их одним альбомом: бот анализирует их как один объект.
6. Подтвердите, что бот правильно определил объект, или нажмите «Я не знаю».
7. Ответьте, что хотите сделать.
8. Если бот просит уточнение, отправьте текст или дополнительное фото.
9. Получите текстовые шаги, отдельные визуальные карточки и общий коллаж.

## API endpoints

- `POST /upload-image` — загрузка фото из Telegram в storage.
- `POST /analyze` — анализ фото и цели пользователя.
- `POST /generate-instruction` — создание JSON-инструкции.
- `POST /generate-images` — генерация карточек шагов.
- `POST /create-collage` — сборка итогового коллажа.
- `GET /instructions/{user_id}` — история инструкций пользователя.

## UX-принципы

Бот не пишет пользователю про поиск мануалов, официальные инструкции или интернет-источники. Внешние статусы звучат так:

- «Анализирую объект…»
- «Проверяю важные детали…»
- «Уточняю, как лучше показать шаги…»
- «Создаю визуальную инструкцию…»

Если важные детали не видны, бот просит простое уточнение: фото сбоку, задней стороны, маркировки или модель.

Если запрос опасный, бот не дает рискованную пошаговую инструкцию и предлагает безопасный вариант.
