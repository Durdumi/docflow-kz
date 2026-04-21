# DocFlow KZ 📄

Платформа автоматизации документооборота и отчётности для казахстанского бизнеса.

## Стек

| Слой | Технология |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic |
| БД | PostgreSQL 16 (schema-per-tenant) |
| Очереди | Celery + Redis |
| Хранилище | MinIO (S3-совместимое) |
| Frontend | React 18 + TypeScript + Vite + Ant Design |
| Контейнеры | Docker Compose |

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
git clone https://github.com/durdumi/docflow-kz.git
cd docflow-kz
cp .env.example .env
# Отредактируй .env под свои настройки
```

### 2. Запустить всё через Docker Compose

```bash
docker-compose up --build
```

### 3. Применить миграции БД

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Открыть в браузере

| Сервис | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/api/docs |
| MinIO Console | http://localhost:9001 |

## Структура проекта

```
docflow-kz/
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── api/v1/       # REST API роутеры
│   │   ├── core/         # Конфиг, БД, безопасность
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы
│   │   ├── services/     # Бизнес-логика
│   │   └── tasks/        # Celery задачи
│   └── alembic/          # Миграции БД
├── frontend/             # React приложение
│   └── src/
│       ├── api/          # API клиент
│       ├── components/   # UI компоненты
│       ├── pages/        # Страницы
│       ├── store/        # Zustand состояние
│       └── i18n/         # Переводы (ru/kk)
├── infra/                # Nginx, PostgreSQL init
└── docker-compose.yml
```

## Разработка

### Backend (без Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install uv
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend (без Docker)

```bash
cd frontend
npm install
npm run dev
```

### Создать миграцию

```bash
docker-compose exec backend alembic revision --autogenerate -m "описание изменений"
docker-compose exec backend alembic upgrade head
```

## Архитектура мультитенантности

Каждая организация получает отдельную PostgreSQL schema:
- `public` — системные таблицы (organizations, users, plans)
- `org_medtech` — данные MedicalTechnologies
- `org_company2` — данные другого клиента

## Роадмап

- [x] **MVP**: Auth, мультитенант, структура проекта
- [ ] Document Builder — шаблоны и создание документов
- [ ] Report Engine — генерация PDF/Excel
- [ ] Import Engine — импорт из 1С и Excel
- [ ] Уведомления — Email + Telegram
- [ ] Workflow — согласование документов
- [ ] ЭЦП — интеграция с NCALayer
- [ ] AI-автозаполнение

## Лицензия

Proprietary — © 2024 Medical Technologies
