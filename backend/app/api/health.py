"""Application health probe endpoints."""

from fastapi import APIRouter, Request, Response
from sqlalchemy import text

from app.core.dashboard_cache import get_dashboard_state
from app.core.device_state_cache import get_all_device_states
from app.db.session import SessionLocal
from app.services.scheduler_service import scheduler

router = APIRouter(tags=["health"])


def get_database_status() -> str:
    """Return the current PostgreSQL dependency status."""

    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return "error"
    finally:
        db.close()

    return "ok"


@router.get("/health/live")
def liveness() -> dict[str, str]:
    """Confirm that the HTTP process is alive."""

    return {
        "status": "alive",
    }


@router.get("/health/ready")
def readiness(response: Response) -> dict[str, str]:
    """Confirm that required request-time dependencies are available."""

    database_status = get_database_status()
    ready = database_status == "ok"

    if not ready:
        response.status_code = 503

    return {
        "status": "ready" if ready else "not_ready",
        "database": database_status,
    }


@router.get("/health/startup")
def startup(
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Confirm that application lifespan initialization completed."""

    startup_complete = bool(
        getattr(
            request.app.state,
            "startup_complete",
            False,
        )
    )

    if not startup_complete:
        response.status_code = 503

    return {
        "status": ("started" if startup_complete else "starting"),
    }


@router.get("/health")
def legacy_health() -> dict[str, object]:
    """Return the backwards-compatible application health response."""

    database_status = get_database_status()
    dashboard_cache = get_dashboard_state()
    device_state_cache = get_all_device_states()

    return {
        "status": ("ok" if database_status == "ok" else "degraded"),
        "database": database_status,
        "scheduler_running": scheduler.running,
        "dashboard_cache_loaded": bool(dashboard_cache),
        "device_state_cache_count": len(device_state_cache),
    }
