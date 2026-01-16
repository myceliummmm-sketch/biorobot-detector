# Mycelium Bot

Telegram бот для Mycelium с Idea Launchpad калькулятором и warming sequences.

## Функции

- **Welcome flow**: /start отправляет приветствие + кнопку Mini App
- **Quiz обработка**: Получает данные из WebApp, определяет блокировку, отправляет персонализированное сообщение
- **Warming sequences**:
  - Sequence A: для тех кто НЕ прошёл квиз (4 часа, день 2, 4, 7)
  - Sequence B: для тех кто прошёл но НЕ начал Vision (день 1-7)

## Установка

1. Клонировать репозиторий
2. Создать `.env` файл (см. `.env.example`)
3. Установить зависимости:

```bash
pip install -r requirements.txt
```

4. Запустить бота:

```bash
python bot.py
```

## Docker

```bash
docker build -t mycelium-bot .
docker run -d --env-file .env mycelium-bot
```

## Конфигурация

| Переменная | Описание |
|------------|----------|
| BOT_TOKEN | Токен бота от @BotFather |
| CALCULATOR_URL | URL калькулятора (Mini App) |
| MYCELIUM_APP_URL | URL главного приложения |
| DATABASE_URL | URL базы данных (SQLite по умолчанию) |

## Добавление видео

1. Отправь видео боту в личку
2. Из ответа бота возьми `message.video.file_id`
3. Вставь в `content/videos.py`

## BotFather настройка

```
/mybots
→ @mdao_community_bot
→ Bot Settings
→ Menu Button
→ Configure Menu Button
→ URL: https://cards.mycelium.gg/quiz
→ Title: Idea Launchpad
```

## Структура проекта

```
mycelium-bot/
├── bot.py              # Основной код бота
├── config.py           # Конфигурация
├── handlers/
│   ├── start.py        # /start handler
│   ├── quiz.py         # WebApp data handler
│   └── sequences.py    # Warming sequences
├── database/
│   ├── models.py       # User model
│   └── db.py           # Database connection
├── content/
│   ├── messages.py     # Тексты сообщений
│   └── videos.py       # Video file_ids
├── requirements.txt
├── Dockerfile
└── README.md
```

---

Made with love by Mycelium Team
