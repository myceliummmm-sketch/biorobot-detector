# 🗄️ Настройка базы данных

## ⚠️ ВАЖНО: Выполните эти шаги ОДИН РАЗ

### Шаг 1: Откройте SQL Editor в Supabase
**Прямая ссылка:** https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio/sql/new

### Шаг 2: Скопируйте и выполните SQL скрипт

1. Откройте файл `migrate_database.sql`
2. Скопируйте ВЕСЬ текст (Cmd+A, Cmd+C)
3. Вставьте в SQL Editor в Supabase (Cmd+V)
4. Нажмите **RUN** (зеленая кнопка)
5. Дождитесь сообщения "Success"

### Шаг 3: Проверьте что таблицы созданы

Выполните этот запрос:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

Должны быть таблицы:
- ✅ users
- ✅ sessions
- ✅ test_results

## ✅ Готово!

После этого приложение будет полностью работать:
- Авторизация через Telegram
- Прохождение теста
- Сохранение результатов в базу

**Тестовая ссылка:** https://biorobot-detector.vercel.app
