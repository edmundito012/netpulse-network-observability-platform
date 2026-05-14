from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.devices import router as devices_router
from app.services.scheduler_service import start_scheduler


app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(devices_router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}