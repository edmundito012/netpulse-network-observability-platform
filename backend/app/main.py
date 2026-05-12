from fastapi import FastAPI

app = FastAPI(
    title="NetPulse API",
    description="Network Observability Platform API",
    version="0.1.0"
)
@app.get("/")
def root():
    return{
        "app": "NetPulse",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}