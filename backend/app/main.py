from fastapi import FastAPI
from app.db.session import engine
from app.models.base import Base

app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.1.0"
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "ok"}