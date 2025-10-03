-- Создание таблиц для Biorobot Detector
-- Выполните этот скрипт в Supabase SQL Editor

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id bigserial PRIMARY KEY,
    telegram_id bigint UNIQUE NOT NULL,
    first_name text NOT NULL,
    last_name text,
    username text,
    created_at timestamp with time zone DEFAULT now()
);

-- Таблица сессий
CREATE TABLE IF NOT EXISTS sessions (
    id bigserial PRIMARY KEY,
    session_token text UNIQUE NOT NULL,
    user_id bigint REFERENCES users(id) ON DELETE CASCADE,
    expires_at timestamp with time zone DEFAULT (now() + interval '24 hours'),
    created_at timestamp with time zone DEFAULT now()
);

-- Таблица результатов тестов
CREATE TABLE IF NOT EXISTS test_results (
    id bigserial PRIMARY KEY,
    user_id bigint REFERENCES users(id) ON DELETE CASCADE,
    score integer NOT NULL,
    result_type text NOT NULL,
    answers jsonb NOT NULL,
    completed_at timestamp with time zone DEFAULT now()
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_test_results_user_id ON test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_test_results_completed_at ON test_results(completed_at);

-- RLS (Row Level Security) политики
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_results ENABLE ROW LEVEL SECURITY;

-- Политики доступа
CREATE POLICY "Users can read own data" ON users FOR SELECT USING (true);
CREATE POLICY "Users can insert own data" ON users FOR INSERT WITH CHECK (true);

CREATE POLICY "Sessions readable by service" ON sessions FOR SELECT USING (true);
CREATE POLICY "Sessions insertable by service" ON sessions FOR INSERT WITH CHECK (true);

CREATE POLICY "Test results readable by service" ON test_results FOR SELECT USING (true);
CREATE POLICY "Test results insertable by service" ON test_results FOR INSERT WITH CHECK (true);