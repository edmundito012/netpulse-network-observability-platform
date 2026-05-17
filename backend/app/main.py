from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.devices import router as devices_router
from app.services.scheduler_service import start_scheduler
from app.api.alerts import router as alerts_router
from app.api.events import router as events_router
from app.api.dashboard import router as dashboard_router
from app.api.websocket import router as websocket_router
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.api.device_state import router as device_state_router

from sqlalchemy import text

from app.core.dashboard_cache import get_dashboard_state
from app.core.device_state_cache import get_all_device_states
from app.db.session import SessionLocal
from app.services.scheduler_service import scheduler
from app.middleware.request_logging import RequestLoggingMiddleware

app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(alerts_router)
app.include_router(events_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)
app.include_router(device_state_router)
app.add_middleware(RequestLoggingMiddleware)

@app.on_event("startup")
def on_startup():
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()

@app.get("/")
def root():
    return {
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
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
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "scheduler_running": scheduler.running,
        "dashboard_cache_loaded": bool(dashboard_cache),
        "device_state_cache_count": len(device_state_cache),
    }