# LangGraph Sales Assistant

Русскоязычный AI-ассистент по продажам для автосервиса на базе LangGraph.

## Возможности

- Ответы на вопросы об услугах и ценах автосервиса
- Загрузка прайс-листа из Google Sheets
- SQLite persistence для сохранения контекста диалога
- Поддержка любого OpenAI-совместимого API
- Интеграция с LangGraph Studio
- Telegram бот

## Установка

```bash
# Установка зависимостей через uv
uv sync
```

## Настройка

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Настройте LLM в `.env`:
```bash
LLM_API_KEY=sk-ваш-ключ
LLM_MODEL=gpt-4o-mini
# LLM_BASE_URL=https://openrouter.ai/api/v1  # опционально
```

Поддерживается любой OpenAI-совместимый API (OpenAI, OpenRouter, Ollama, Groq и др.)

## Запуск в LangGraph Studio

```bash
# Запуск dev-сервера
uv run langgraph dev
```

Откройте в браузере ссылку из консоли (обычно https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024).

В Studio выберите граф `python-ai-agent` и начните диалог.

## Примеры вопросов

- "Какие услуги у вас есть?"
- "Сколько стоит диагностика двигателя?"
- "Подскажите услуги по ремонту подвески"
- "Что по тормозам?"
- "Замена масла в двигателе - сколько?"

## Telegram бот

**Попробовать:** [@assistant_test_task_bot](https://t.me/assistant_test_task_bot) — демо-бот для тестирования работы ассистента

### Локальный запуск (опционально)

1. Создайте бота через @BotFather в Telegram и получите токен

2. Добавьте токен в `.env`:
```bash
TELEGRAM_BOT_TOKEN=ваш-токен
```

3. Запустите бота:
```bash
uv run python -m src.bot
```

## Структура проекта

```
src/
├── __init__.py        # Пакет
├── config.py          # Настройки: LLM провайдеры, модели данных
├── data_loader.py     # Загрузка прайса (Google Sheets)
├── tools.py           # Инструменты поиска услуг
├── agent.py           # LangGraph агент + системный промпт
├── bot.py             # Telegram бот
└── main.py            # Entry point для Studio
```
