"""NetPulse FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest
from sqlalchemy import text

from app.api.router import router as application_router
from app.core.dashboard_cache import get_dashboard_state
from app.core.device_state_cache import get_all_device_states
from app.core.logging import logger
from app.db.session import SessionLocal
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.scheduler_service import (
    scheduler,
    start_scheduler,
    stop_scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop application-owned resources."""

    logger.info("Starting NetPulse application")

    start_scheduler()

    yield

    logger.info("Stopping NetPulse application")

    stop_scheduler()


app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(application_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return basic application metadata."""

    return {
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, object]:
    """Return current application dependency health."""

    db_status = "ok"
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        db.close()

    dashboard_cache = get_dashboard_state()
    device_state_cache = get_all_device_states()

    return {
        "status": ("ok" if db_status == "ok" else "degraded"),
        "database": db_status,
        "scheduler_running": scheduler.running,
        "dashboard_cache_loaded": bool(dashboard_cache),
        "device_state_cache_count": len(device_state_cache),
    }


@app.get("/metrics")
def metrics() -> Response:
    """Expose NetPulse Prometheus metrics."""

    return Response(
        generate_latest(),
        media_type="text/plain",
    )
