# 🤖 Biorobot Detector

**Интерактивный тест на человечность с Telegram авторизацией**

## 🚀 Быстрый старт

**Рабочая ссылка:** https://biorobot-detector.vercel.app

**Telegram бот:** https://t.me/mdao_community_bot

## ✨ Возможности

- ✅ Telegram авторизация (или demo режим)
- ✅ 10 научно обоснованных вопросов
- ✅ 10 типов результатов от "Биоробот 🤖" до "Легендарный Человек 🦄"
- ✅ PostgreSQL база данных (Supabase)
- ✅ Русский/Английский интерфейс
- ✅ Адаптивный дизайн
- ✅ Duolingo-style UI

## 🛠️ Технологии

- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript
- **Backend:** Vercel Functions (Node.js)
- **Database:** PostgreSQL (Supabase)
- **Auth:** Telegram Web App API

## 📁 Структура

```
biorobot-app/
├── index.html              # Фронтенд приложения
├── api/
│   ├── auth/telegram.js    # API авторизации
│   └── test/result.js      # API сохранения результатов
├── setup_database.sql      # SQL для создания таблиц
├── vercel.json            # Конфигурация Vercel
└── .env                   # Переменные окружения
```

## 🔧 Настройка (если нужно задеплоить свою версию)

1. **Создать Supabase проект:** https://supabase.com
2. **Выполнить SQL скрипт** `setup_database.sql` в Supabase SQL Editor
3. **Форкнуть/клонировать репозиторий**
4. **Задеплоить на Vercel:**
   ```bash
   vercel deploy
   ```
5. **Добавить переменные окружения в Vercel:**
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`

## 📊 Панели управления

- **Vercel:** https://vercel.com/myceliummmm-sketch/biorobot-detector
- **Supabase:** https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio

## 🎯 Как работает

1. Пользователь авторизуется через Telegram (или demo режим)
2. Проходит тест из 10 вопросов
3. Получает результат (0-40 баллов)
4. Результат сохраняется в базе данных
5. Может поделиться результатом в Telegram

## ✅ Статус

**РАБОТАЕТ!** Последняя проверка: 4 октября 2025

---

Made with ❤️ by Mycelium Team
