"""NetPulse FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest

from app.api.health import router as health_router
from app.api.router import router as application_router
from app.core.logging import logger
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.scheduler_service import (
    start_scheduler,
    stop_scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop application-owned resources."""

    logger.info("Starting NetPulse application")

    start_scheduler()
    app.state.startup_complete = True

    try:
        yield
    finally:
        app.state.startup_complete = False

        logger.info("Stopping NetPulse application")

        stop_scheduler()


app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.5.0",
    lifespan=lifespan,
)

app.state.startup_complete = False

app.add_middleware(RequestLoggingMiddleware)
app.include_router(health_router)
app.include_router(application_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return basic application metadata."""

    return {
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/metrics")
def metrics() -> Response:
    """Expose NetPulse Prometheus metrics."""

    return Response(
        generate_latest(),
        media_type="text/plain",
    )
