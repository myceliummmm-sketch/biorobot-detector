# 🤖 Biorobot Detector - Структура проекта

## 📁 Файлы проекта

### 🎯 Главные файлы
- **index.html** - Основное веб-приложение (фронтенд + логика)
- **vercel.json** - Конфигурация деплоя на Vercel
- **package.json** - Зависимости проекта

### 🔌 API Endpoints (Vercel Functions)
- **api/auth/telegram.js** - Авторизация через Telegram
- **api/test/result.js** - Сохранение результатов теста

### 🗄️ База данных
- **setup_database.sql** - SQL скрипт для создания таблиц в Supabase
- **.env** - Переменные окружения (Supabase URL и ключи)

### 📚 Документация
- **README.md** - Главная документация проекта
- **SETUP_INSTRUCTIONS.md** - Инструкции по настройке
- **LINKS.md** - Все полезные ссылки проекта
- **TELEGRAM_SETUP.md** - Настройка Telegram бота

## 🏗️ Архитектура

```
Frontend (index.html)
    ↓
Telegram Web App API
    ↓
Vercel Functions (API)
    ↓
Supabase (PostgreSQL Database)
```

## 🔄 Как работает:

1. **Пользователь открывает приложение** через Telegram или браузер
2. **Telegram авторизация** → `api/auth/telegram.js` → создает/обновляет пользователя и сессию
3. **Прохождение теста** → 10 вопросов с вариантами ответов
4. **Подсчет баллов** → определение типа результата (0-40 баллов)
5. **Сохранение результата** → `api/test/result.js` → запись в БД
6. **Показ результата** → с возможностью поделиться в Telegram

## 🗃️ База данных Supabase

### Таблицы:
- **users** - Пользователи из Telegram
- **sessions** - Активные сессии пользователей
- **test_results** - Результаты прохождения тестов

## 🌐 Ссылки

- **Приложение:** https://biorobot-detector.vercel.app
- **Telegram Bot:** https://t.me/mdao_community_bot
- **Vercel Dashboard:** https://vercel.com/myceliummmm-sketch/biorobot-detector
- **Supabase Dashboard:** https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio

## ✅ Статус: Работает!

Последняя проверка: Fri Oct 4 00:08:00 +03 2025
