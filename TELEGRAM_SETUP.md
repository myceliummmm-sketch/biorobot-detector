# 🤖 Настройка Telegram бота для авторизации

## Быстрая настройка:

### 1. Создайте бота через @BotFather
1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Введите имя бота: `Biorobot Detector`
4. Введите username: `biorobot_detector_bot` (или любой доступный)
5. Получите BOT_TOKEN

### 2. Настройте домен для авторизации
1. Напишите @BotFather команду `/setdomain`
2. Выберите вашего бота
3. Введите домен: `localhost:3000` (для разработки) или ваш реальный домен

### 3. Обновите конфигурацию
Замените в файле `.env`:
```
BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
```

### 4. Обновите имя бота в коде
В файле `public/index.html` строка 695:
```javascript
script.setAttribute('data-telegram-login', 'ваш_bot_username');
```

### 5. Перезапустите сервер
```bash
npm start
```

## Готово!
Теперь на странице http://localhost:3000 будет настоящая Telegram авторизация вместо тестовой.

## Для продакшена:
- Замените `localhost:3000` на ваш реальный домен
- Обновите BOT_TOKEN на продакшн токен
- Деплойте на Vercel/Railway/Render