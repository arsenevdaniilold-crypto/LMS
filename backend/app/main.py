from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.limiter import limiter
from app.routers import health
from app.routers import auth, users, classes, announcements, assignments, solutions
from app.routers import notifications, ws, admin
from app.services.minio_storage import minio_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    minio_storage.ensure_bucket()
    yield


API_DESCRIPTION = """
Learning Management System API.

## Аутентификация
JWT в httpOnly-cookie: `access_token` (30 мин) и `refresh_token` (7 дней,
path=`/api/auth`). Залогиньтесь через `POST /api/auth/login` — браузер сам
будет слать cookie. При истечении access-токена дёрните `POST /api/auth/refresh`.

## Формат ошибок
Все ошибки имеют единое тело:

```json
{ "detail": { "code": "MACHINE_CODE", "message": "Human readable text" } }
```

`code` — стабильный машиночитаемый идентификатор (например `INVALID_CREDENTIALS`,
`GRADE_OUT_OF_RANGE`, `MEAN_MISMATCH`, `FORBIDDEN`), `message` — пояснение.
Ошибки валидации Pydantic приходят с `code = "VALIDATION_ERROR"` и статусом 422.
"""

TAGS_METADATA = [
    {"name": "auth", "description": "Регистрация, вход, выход, ротация токенов."},
    {"name": "users", "description": "Профиль текущего пользователя."},
    {"name": "classes", "description": "Классы, участники, приглашения, вступление."},
    {"name": "announcements", "description": "Объявления в классе и вложения."},
    {"name": "assignments", "description": "Задания, материалы, группы (auto/manual)."},
    {"name": "solutions", "description": "Решения, статусы, оценивание, перераспределение, сводка оценок."},
    {"name": "notifications", "description": "In-app уведомления (список и отметка прочитанным)."},
    {"name": "admin", "description": "Администрирование: пользователи, классы, статистика."},
    {"name": "health", "description": "Проверка живости сервиса."},
]

app = FastAPI(
    title="LMS API",
    version="1.0.0",
    description=API_DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(classes.router)
app.include_router(announcements.router)
app.include_router(assignments.router)
app.include_router(solutions.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(ws.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    return JSONResponse(
        status_code=422,
        content={"detail": {"code": "VALIDATION_ERROR", "message": first.get("msg", "Validation error")}},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )


@app.get("/")
async def root():
    return {"message": "LMS API"}
