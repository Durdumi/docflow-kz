-- DocFlow KZ — инициализация БД
-- Этот скрипт выполняется при первом старте контейнера PostgreSQL

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- для полнотекстового поиска

-- Убеждаемся что public schema существует
CREATE SCHEMA IF NOT EXISTS public;

-- Комментарий к БД
COMMENT ON DATABASE docflow IS 'DocFlow KZ — платформа автоматизации документооборота';
