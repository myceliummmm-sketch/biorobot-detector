const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const bodyParser = require('body-parser');
const crypto = require('crypto');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// База данных
const db = new sqlite3.Database('./biorobot.db');

// Создание таблиц
db.serialize(() => {
    // Таблица пользователей
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        photo_url TEXT,
        auth_date INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Таблица результатов тестов
    db.run(`CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        result_type TEXT,
        answers TEXT,
        completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )`);

    // Таблица сессий
    db.run(`CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )`);
});

// Функция проверки Telegram авторизации
function verifyTelegramAuth(authData, botToken) {
    const secret = crypto.createHmac('sha256', 'WebAppData').update(botToken).digest();

    const { hash, ...data } = authData;
    const dataCheckString = Object.keys(data)
        .sort()
        .map(key => `${key}=${data[key]}`)
        .join('\n');

    const calculatedHash = crypto.createHmac('sha256', secret).update(dataCheckString).digest('hex');

    return calculatedHash === hash && Date.now() / 1000 - data.auth_date < 86400; // 24 часа
}

// API Routes

// Telegram авторизация
app.post('/api/auth/telegram', (req, res) => {
    const authData = req.body;

    // В продакшене здесь должна быть проверка с реальным bot token
    // const isValid = verifyTelegramAuth(authData, process.env.BOT_TOKEN);
    // if (!isValid) {
    //     return res.status(401).json({ error: 'Invalid authorization' });
    // }

    const { id, first_name, last_name, username, photo_url, auth_date } = authData;

    // Поиск или создание пользователя
    db.get(`SELECT * FROM users WHERE telegram_id = ?`, [id], (err, user) => {
        if (err) {
            return res.status(500).json({ error: 'Database error' });
        }

        if (user) {
            // Пользователь существует, обновляем данные
            db.run(`UPDATE users SET
                first_name = ?, last_name = ?, username = ?, photo_url = ?, auth_date = ?
                WHERE telegram_id = ?`,
                [first_name, last_name, username, photo_url, auth_date, id],
                function(err) {
                    if (err) {
                        return res.status(500).json({ error: 'Update error' });
                    }

                    // Создаем сессию
                    const sessionId = crypto.randomBytes(32).toString('hex');
                    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 часа

                    db.run(`INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)`,
                        [sessionId, user.id, expiresAt.toISOString()],
                        function(err) {
                            if (err) {
                                return res.status(500).json({ error: 'Session error' });
                            }

                            res.json({
                                sessionId,
                                user: {
                                    id: user.id,
                                    telegram_id: id,
                                    first_name,
                                    last_name,
                                    username,
                                    photo_url
                                }
                            });
                        }
                    );
                }
            );
        } else {
            // Создаем нового пользователя
            db.run(`INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, auth_date)
                VALUES (?, ?, ?, ?, ?, ?)`,
                [id, first_name, last_name, username, photo_url, auth_date],
                function(err) {
                    if (err) {
                        return res.status(500).json({ error: 'User creation error' });
                    }

                    // Создаем сессию
                    const sessionId = crypto.randomBytes(32).toString('hex');
                    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000);

                    db.run(`INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)`,
                        [sessionId, this.lastID, expiresAt.toISOString()],
                        function(err) {
                            if (err) {
                                return res.status(500).json({ error: 'Session error' });
                            }

                            res.json({
                                sessionId,
                                user: {
                                    id: this.lastID,
                                    telegram_id: id,
                                    first_name,
                                    last_name,
                                    username,
                                    photo_url
                                }
                            });
                        }
                    );
                }
            );
        }
    });
});

// Middleware для проверки сессии
function requireAuth(req, res, next) {
    const sessionId = req.headers['x-session-id'];

    if (!sessionId) {
        return res.status(401).json({ error: 'No session provided' });
    }

    db.get(`SELECT s.*, u.* FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = ? AND s.expires_at > datetime('now')`,
            [sessionId], (err, result) => {
        if (err || !result) {
            return res.status(401).json({ error: 'Invalid session' });
        }

        req.user = {
            id: result.user_id,
            telegram_id: result.telegram_id,
            first_name: result.first_name,
            last_name: result.last_name,
            username: result.username,
            photo_url: result.photo_url
        };

        next();
    });
}

// Сохранение результата теста
app.post('/api/test/result', requireAuth, (req, res) => {
    const { score, result_type, answers } = req.body;

    db.run(`INSERT INTO test_results (user_id, score, result_type, answers)
            VALUES (?, ?, ?, ?)`,
            [req.user.id, score, result_type, JSON.stringify(answers)],
            function(err) {
                if (err) {
                    return res.status(500).json({ error: 'Failed to save result' });
                }

                res.json({
                    id: this.lastID,
                    score,
                    result_type,
                    saved: true
                });
            }
    );
});

// Получение результатов пользователя
app.get('/api/test/results', requireAuth, (req, res) => {
    db.all(`SELECT * FROM test_results WHERE user_id = ? ORDER BY completed_at DESC`,
           [req.user.id], (err, results) => {
        if (err) {
            return res.status(500).json({ error: 'Failed to fetch results' });
        }

        res.json(results.map(result => ({
            id: result.id,
            score: result.score,
            result_type: result.result_type,
            completed_at: result.completed_at
        })));
    });
});

// Получение статистики
app.get('/api/stats', (req, res) => {
    const queries = [
        'SELECT COUNT(*) as total_users FROM users',
        'SELECT COUNT(*) as total_tests FROM test_results',
        'SELECT AVG(score) as avg_score FROM test_results',
        'SELECT result_type, COUNT(*) as count FROM test_results GROUP BY result_type'
    ];

    Promise.all(queries.map(query =>
        new Promise((resolve, reject) => {
            db.all(query, (err, result) => {
                if (err) reject(err);
                else resolve(result);
            });
        })
    )).then(([totalUsers, totalTests, avgScore, resultTypes]) => {
        res.json({
            total_users: totalUsers[0].total_users,
            total_tests: totalTests[0].total_tests,
            avg_score: Math.round(avgScore[0].avg_score * 100) / 100,
            result_distribution: resultTypes
        });
    }).catch(err => {
        res.status(500).json({ error: 'Failed to fetch stats' });
    });
});

// Главная страница
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Запуск сервера
app.listen(PORT, () => {
    console.log(`🤖 Biorobot Detector server running on port ${PORT}`);
    console.log(`📱 Open http://localhost:${PORT} to start testing`);
});

module.exports = app;