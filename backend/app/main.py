"""NetPulse FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest
from sqlalchemy import text

from app.api.alerts import router as alerts_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.business_impact import (
    router as business_impact_router,
)
from app.api.dashboard import router as dashboard_router
from app.api.device_risk import router as device_risk_router
from app.api.device_state import router as device_state_router
from app.api.devices import router as devices_router
from app.api.events import router as events_router
from app.api.experience_summary import (
    router as experience_summary_router,
)
from app.api.gaming_experience import (
    router as gaming_experience_router,
)
from app.api.gaming_impact import router as gaming_impact_router
from app.api.metric_series import router as metric_series_router
from app.api.network_anomalies import (
    router as network_anomalies_router,
)
from app.api.network_health_score import (
    router as network_health_score_router,
)
from app.api.network_impact import router as network_impact_router
from app.api.network_quality import (
    router as network_quality_router,
)
from app.api.network_risk import router as network_risk_router
from app.api.network_trends import router as network_trends_router
from app.api.notifications import router as notifications_router
from app.api.portfolio_dashboard import (
    router as portfolio_dashboard_router,
)
from app.api.sla import router as sla_router
from app.api.streaming_experience import (
    router as streaming_experience_router,
)
from app.api.users import router as users_router
from app.api.video_call_experience import (
    router as video_call_router,
)
from app.api.websocket import router as websocket_router
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
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(audit_logs_router)
app.include_router(devices_router)
app.include_router(alerts_router)
app.include_router(events_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)
app.include_router(device_state_router)
app.include_router(network_impact_router)
app.include_router(business_impact_router)
app.include_router(gaming_impact_router)
app.include_router(network_risk_router)
app.include_router(device_risk_router)
app.include_router(notifications_router)
app.include_router(gaming_experience_router)
app.include_router(streaming_experience_router)
app.include_router(experience_summary_router)
app.include_router(network_quality_router)
app.include_router(video_call_router)
app.include_router(network_trends_router)
app.include_router(network_anomalies_router)
app.include_router(network_health_score_router)
app.include_router(sla_router)
app.include_router(metric_series_router)
app.include_router(portfolio_dashboard_router)


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
        "status": (
            "ok"
            if db_status == "ok"
            else "degraded"
        ),
        "database": db_status,
        "scheduler_running": scheduler.running,
        "dashboard_cache_loaded": bool(dashboard_cache),
        "device_state_cache_count": len(
            device_state_cache
        ),
    }


@app.get("/metrics")
def metrics() -> Response:
    """Expose NetPulse Prometheus metrics."""

    return Response(
        generate_latest(),
        media_type="text/plain",
    )