# 🚀 Инструкции по завершению настройки Biorobot Detector

## 📋 ШАГ 1: Создать таблицы в Supabase

### 🔗 Прямые ссылки:
- **SQL Editor:** https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio/sql/new
- **SQL код:** https://github.com/myceliummmm-sketch/biorobot-detector/blob/main/setup_database.sql

### 📝 Пошагово:
1. **Откройте SQL Editor** по ссылке выше
2. **Откройте файл с SQL кодом** по второй ссылке
3. **Скопируйте ВЕСЬ код** из файла `setup_database.sql` (Ctrl+A → Ctrl+C)
4. **Вставьте в SQL Editor** (Ctrl+V)
5. **Нажмите зеленую кнопку "Run"**
6. **Дождитесь сообщения об успехе** (Success)

## 🔧 ШАГ 2: Настроить переменные окружения в Vercel

### 🔗 Прямая ссылка:
- **Environment Variables:** https://vercel.com/myceliummmm-sketch/biorobot-detector/settings/environment-variables

### 📝 Пошагово:
1. **Откройте настройки** по ссылке выше
2. **Нажмите "Add"** (добавить переменную)
3. **Добавьте первую переменную:**
   - Name: `SUPABASE_URL`
   - Value: `https://qglmebqnyrauqcamhwio.supabase.co`
   - Environments: выберите все (Production, Preview, Development)
   - **Нажмите "Save"**

4. **Добавьте вторую переменную:**
   - Name: `SUPABASE_ANON_KEY`
   - Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFnbG1lYnFueXJhdXFjYW1od2lvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0MDY2ODUsImV4cCI6MjA3NDk4MjY4NX0.k_OEuXEUscoasAy_W_YfhFCXr9iXOqjjP9vgJuQ7jnA`
   - Environments: выберите все (Production, Preview, Development)
   - **Нажмите "Save"**

5. **Сохраните настройки и перезапустите деплой**

## ✅ ШАГ 3: Проверить работу

### 🔗 Прямые ссылки для тестирования:
- **Web App:** https://biorobot-detector.vercel.app
- **Telegram Web App:** https://t.me/mdao_community_bot/biorobot_detector
- **Supabase Tables:** https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio/editor

### 📝 Пошагово:
1. **Откройте приложение** по первой ссылке
2. **Протестируйте через Telegram Web App** по второй ссылке
3. **Проверьте сохранение данных** в Supabase по третьей ссылке

## 🎯 Готово!

После выполнения этих шагов приложение будет полностью функциональным с:
- ✅ Полноценной базой данных PostgreSQL
- ✅ Сохранением пользователей и результатов тестов
- ✅ API endpoints для всех операций
- ✅ Telegram Web App интеграцией

Все файлы готовы, нужно только выполнить эти 3 простых шага!