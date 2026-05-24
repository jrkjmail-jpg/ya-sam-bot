# Размещение бота «Я сам»

Этот проект состоит из двух частей:

- FastAPI backend — принимает фото, хранит файлы, вызывает AI и собирает инструкцию.
- Telegram bot — общается с пользователем и вызывает backend.

В продакшене лучше использовать PostgreSQL/Supabase и Supabase Storage. Локальное хранилище подходит для MVP и тестов, но на некоторых хостингах файлы могут пропадать после перезапуска.

## 1. Что подготовить

Нужны:

- Telegram bot token от BotFather.
- OpenAI API key.
- PostgreSQL или Supabase database URL.
- Supabase Storage bucket, если API и бот будут запущены разными сервисами.
- GitHub-репозиторий с кодом.

Не публикуйте `.env` в GitHub. В репозитории должен быть только `.env.example`.

## 2. Переменные окружения

Обязательные:

```env
TELEGRAM_BOT_TOKEN=123456:telegram_token
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+psycopg://user:password@host:5432/db
API_BASE_URL=https://your-api-domain.com
USE_MOCK_AI=false
```

Для Supabase Storage:

```env
SUPABASE_URL=https://project.supabase.co
SUPABASE_KEY=service_role_or_storage_key
STORAGE_BUCKET=yasam
```

Модели:

```env
OPENAI_TEXT_MODEL=gpt-5-mini
OPENAI_IMAGE_MODEL=gpt-image-1
```

Для первого smoke test можно временно включить:

```env
USE_MOCK_AI=true
```

## 3. Вариант A: один процесс на бот-хостинге

Подходит для хостингов, где можно запустить одну Python-команду.

Start command:

```bash
python -m scripts.run_all
```

Что делает команда:

- запускает FastAPI на порту из `PORT` или `8000`;
- запускает Telegram-бота в polling-режиме;
- использует один общий локальный `storage/`.

Минимальные настройки:

```env
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
DATABASE_URL=sqlite:///./yasam.db
API_BASE_URL=http://localhost:8000
USE_MOCK_AI=false
```

Для демо это самый простой путь. Для стабильного продакшена лучше заменить SQLite на PostgreSQL.

## 4. Вариант B: два сервиса на Render/Railway/Amvera

Создайте из одного GitHub-репозитория два сервиса.

### API service

Type: Web service

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Переменные:

```env
OPENAI_API_KEY=...
DATABASE_URL=postgresql+psycopg://...
API_BASE_URL=https://your-api-domain.com
SUPABASE_URL=...
SUPABASE_KEY=...
STORAGE_BUCKET=yasam
USE_MOCK_AI=false
```

### Bot worker

Type: Worker / Background service

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m bot.main
```

Переменные:

```env
TELEGRAM_BOT_TOKEN=...
API_BASE_URL=https://your-api-domain.com
```

Если API и бот разнесены по разным сервисам, подключите Supabase Storage. Иначе bot worker не увидит локальные файлы API после генерации карточек.

## 5. Вариант C: VPS или Docker-хостинг

На сервере:

```bash
git clone https://github.com/OWNER/REPO.git
cd REPO
cp .env.example .env
nano .env
docker compose up --build -d
```

Проверка API:

```bash
curl http://SERVER_IP:8000/health
```

Если домен подключен через reverse proxy, укажите:

```env
API_BASE_URL=https://bot-api.your-domain.com
```

## 6. Проверка полного сценария

1. Откройте Telegram-бота.
2. Отправьте `/start`.
3. Пришлите фото.
4. Напишите цель: например, «как закрепить это».
5. Дождитесь анализа.
6. Если бот просит уточнение, пришлите фото сбоку или напишите модель.
7. Проверьте, что пришли текстовые шаги, карточки и итоговый коллаж.

## 7. Частые проблемы

### Бот не отвечает

Проверьте:

- правильный `TELEGRAM_BOT_TOKEN`;
- что запущен worker или `scripts.run_all`;
- логи процесса бота.

### API не открывается

Проверьте:

- start command для API;
- переменную `PORT`;
- endpoint `/health`.

### Картинки не отправляются

Если API и бот в разных сервисах, включите Supabase Storage:

```bash
pip install -r requirements-supabase.txt
```

И заполните:

```env
SUPABASE_URL=
SUPABASE_KEY=
STORAGE_BUCKET=
```

### OpenAI не генерирует

Проверьте:

- `OPENAI_API_KEY`;
- доступность моделей;
- баланс и лимиты аккаунта;
- логи API.

### Нужно проверить без OpenAI

Поставьте:

```env
USE_MOCK_AI=true
```

Бот пройдет сценарий с тестовой инструкцией и placeholder-картинками.

## 8. Рекомендованный порядок запуска MVP

1. Сначала запустить локально с `USE_MOCK_AI=true`.
2. Потом локально с настоящим `OPENAI_API_KEY`.
3. Потом залить на GitHub.
4. Потом развернуть один процесс через `python -m scripts.run_all`.
5. После первого демо перейти на PostgreSQL и Supabase Storage.
