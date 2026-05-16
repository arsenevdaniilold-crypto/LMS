# LMS — Система управления учебным процессом

## Быстрый старт

```bash
# 1. Скопируй .env.example в .env и при необходимости измени значения
cp .env.example .env

# 2. Подними все сервисы
docker compose up --build

# 3. Примени миграции (в другом терминале)
docker compose exec backend alembic upgrade head
```

После запуска:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Minio Console: http://localhost:9001 (admin: minioadmin / minioadmin123)

## Стек

| Слой | Технология |
|---|---|
| Backend | Python 3.13 + FastAPI + SQLAlchemy 2.0 + Alembic |
| Frontend | Vue 3 + Vite + Pinia + TypeScript |
| БД | PostgreSQL 16 |
| Файлы | Minio |

## Структура

```
lms/
├── backend/        # FastAPI приложение
├── frontend/       # Vue 3 приложение
├── docker-compose.yml
├── .env.example
└── PROJECT_PLAN.md
```

## Миграции

```bash
# Применить все миграции
docker compose exec backend alembic upgrade head

# Откатить последнюю
docker compose exec backend alembic downgrade -1

# Создать новую миграцию
docker compose exec backend alembic revision --autogenerate -m "description"
```

## Переменные окружения

Все переменные описаны в `.env.example`.
