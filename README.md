# LMS — Система управления учебным процессом

Learning Management System: классы, задания (индивидуальные и групповые),
решения с оцениванием и перераспределением оценок внутри группы, in-app
уведомления через WebSocket, админ-панель.

| Слой | Технология |
|---|---|
| Backend | Python 3.13 + FastAPI + SQLAlchemy 2.0 (async) + Alembic |
| Frontend | Vue 3 (Composition API) + Vite + Pinia + TypeScript |
| БД | PostgreSQL 16 |
| Файлы | Minio (presigned URLs) |
| Auth | JWT (access 30 мин / refresh 7 дн) в httpOnly cookie |
| Realtime | FastAPI WebSocket |

## Быстрый старт (разработка)

```bash
# 1. Скопируй .env.example в .env (при необходимости измени значения)
cp .env.example .env

# 2. Подними все сервисы
docker compose up --build

# 3. Применить миграции (в другом терминале)
docker compose exec backend alembic upgrade head
```

После запуска:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc
- Minio Console: http://localhost:9001 (admin: `minioadmin` / `minioadmin123`)

Сделать пользователя админом:

```bash
docker compose exec postgres psql -U lms_user -d lms \
  -c "UPDATE users SET is_admin = true WHERE email = 'you@example.com';"
```

## Формат ошибок

Все ошибки API возвращаются единым телом:

```json
{ "detail": { "code": "MACHINE_CODE", "message": "Human readable text" } }
```

- `code` — стабильный машиночитаемый идентификатор. Фронтенд опирается на него,
  а не на текст. Примеры: `INVALID_CREDENTIALS`, `EMAIL_TAKEN`, `FORBIDDEN`,
  `GRADE_OUT_OF_RANGE`, `MEAN_MISMATCH`, `MEMBER_MISMATCH`, `INVALID_TRANSITION`,
  `SOLUTION_EXISTS`, `DEADLINE_PASSED`.
- `message` — человекочитаемое пояснение.
- Ошибки валидации Pydantic — статус `422`, `code = "VALIDATION_ERROR"`.

На фронтенде разбор делает `extractError()` (`frontend/src/shared/api/errors.ts`).

## Тесты

**Backend** (pytest, запускается в контейнере — там есть зависимости и доступ к
Postgres; создаётся отдельная БД `lms_test`, каждый тест в откатываемой транзакции):

```bash
docker compose exec backend python -m pytest tests/ -v
```

Покрытие: unit на security/files/invite, и интеграция через ASGI —
auth-флоу, жизненный цикл индивидуального решения, валидация перераспределения
(среднее ±0.005, покрытие всех участников, диапазон оценки).

**Frontend** (Vitest — чистая логика перераспределения):

```bash
docker compose exec frontend npx vitest run
```

**Smoke-тест** (сквозной happy-path по живому API):

```bash
docker compose exec backend python scripts/smoke_test.py
```

## Миграции

```bash
docker compose exec backend alembic upgrade head        # применить все
docker compose exec backend alembic downgrade -1        # откатить последнюю
docker compose exec backend alembic revision --autogenerate -m "description"
```

## Production

Прод-конфигурация (`docker-compose.prod.yml`) собирает неизменяемые образы, не
монтирует исходники, запускает backend без `--reload`, фронтенд отдаётся через
nginx (со SPA-fallback и проксированием `/api`, `/health`, `/ws`), а порт
Postgres наружу не публикуется.

```bash
# 1. Подготовь прод-окружение
cp .env.prod.example .env.prod      # затем заполни секреты и публичные хосты

# 2. Собери и подними
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 3. Применить миграции
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Фронтенд будет доступен на `http://<host>:${FRONTEND_PORT:-80}`.

> **Minio в проде.** Порт S3 (`9000`) остаётся опубликованным: presigned-ссылки
> на скачивание подписываются под `MINIO_PUBLIC_ENDPOINT` и должны быть доступны
> браузеру. Укажи в `.env.prod` реально доступный хост. Админ-консоль (`9001`)
> наружу не выставляется.

## Структура

```
lms/
├── backend/                 # FastAPI приложение (app/), тесты (tests/), smoke (scripts/)
├── frontend/                # Vue 3 приложение (src/), nginx.conf, Dockerfile.prod
├── docker-compose.yml       # dev
├── docker-compose.prod.yml  # prod
├── .env.example / .env.prod.example
└── PROJECT_PLAN.md
```

## Переменные окружения

Dev — в `.env.example`, prod — в `.env.prod.example` (с пояснениями по каждой).
