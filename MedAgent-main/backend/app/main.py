from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import limiter
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import register_middlewares
from app.modules.admin.router import admin_router
from app.modules.auth.router import router as auth_router
from app.modules.conversations.chat import chat_router
from app.modules.conversations.router import router as conversations_router
from app.modules.doctors.router import doctors_router
from app.modules.handoff.router import handoff_router
from app.modules.notifications.router import router as notifications_router
from app.modules.support.router import support_router
from app.modules.users.router import router as users_router

setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio as _asyncio

    logger.info("startup", env=settings.ENV, version=settings.VERSION)

    # PHI encryption check — fail-fast in production
    if settings.is_production:
        from app.core.encryption import is_encryption_enabled

        if not is_encryption_enabled():
            raise RuntimeError(
                "PHI_ENCRYPTION_ENABLED must be 'true' and DATA_ENCRYPTION_KEY must be set in production"
            )

    # ── Background notification scheduler ──
    _scheduler_task: _asyncio.Task | None = None

    async def _notification_worker():
        """Periodically process due queued notifications."""
        while True:
            try:
                await _asyncio.sleep(settings.NOTIFICATION_POLL_INTERVAL_SECONDS)
                from app.modules.notifications.service import process_due_notifications

                result = await process_due_notifications()
                if result["processed"] > 0:
                    logger.info(
                        "notification_worker_cycle",
                        processed=result["processed"],
                        sent=result["sent"],
                        failed=result["failed"],
                    )
            except Exception:
                logger.exception("notification_worker_error")

    _scheduler_task = _asyncio.create_task(_notification_worker())

    yield

    if _scheduler_task:
        _scheduler_task.cancel()
        with suppress(_asyncio.CancelledError):
            await _scheduler_task

    logger.info("shutdown")


app = FastAPI(
    title="MedAgent API",
    version=settings.VERSION,
    docs_url=None,
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

if not settings.is_production:
    _static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )


register_exception_handlers(app)
register_middlewares(app, settings.CORS_ORIGINS)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    from slowapi import _rate_limit_exceeded_handler

    return _rate_limit_exceeded_handler(request, exc)


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(handoff_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(support_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.get("/api/v1/health/ready", tags=["meta"])
async def health_ready():
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unhealthy"
    status = "ready" if db_status == "ok" else "degraded"
    return {"status": status, "checks": {"db": db_status}}


@app.get("/api/v1/version", tags=["meta"])
async def version():
    return {
        "version": settings.VERSION,
        "env": settings.ENV,
        "commit": settings.COMMIT_SHA,
    }
