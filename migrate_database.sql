-- МИГРАЦИЯ БАЗЫ ДАННЫХ - Выполнить в Supabase SQL Editor
-- https://supabase.com/dashboard/project/qglmebqnyrauqcamhwio/sql/new

-- 1. Удалить старые таблицы если есть
DROP TABLE IF EXISTS test_results CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. Создать таблицы заново
CREATE TABLE users (
    id bigserial PRIMARY KEY,
    telegram_id bigint UNIQUE NOT NULL,
    first_name text NOT NULL,
    last_name text,
    username text,
    language_code text DEFAULT 'ru',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE sessions (
    id bigserial PRIMARY KEY,
    session_token text UNIQUE NOT NULL,
    user_id bigint REFERENCES users(id) ON DELETE CASCADE,
    expires_at timestamp with time zone DEFAULT (now() + interval '24 hours'),
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE test_results (
    id bigserial PRIMARY KEY,
    user_id bigint REFERENCES users(id) ON DELETE CASCADE,
    score integer NOT NULL,
    result_type text NOT NULL,
    answers jsonb NOT NULL,
    completed_at timestamp with time zone DEFAULT now()
);

-- 3. Создать индексы
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_sessions_session_token ON sessions(session_token);
CREATE INDEX idx_test_results_user_id ON test_results(user_id);
CREATE INDEX idx_test_results_completed_at ON test_results(completed_at);

-- 4. Включить RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_results ENABLE ROW LEVEL SECURITY;

-- 5. Создать политики доступа (разрешить всем для демо)
CREATE POLICY "Allow all for users" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for sessions" ON sessions FOR ALL USING (true);
CREATE POLICY "Allow all for test_results" ON test_results FOR ALL USING (true);

-- ГОТОВО! Теперь база готова к работе.
