"""Version 1 API router registry."""

from fastapi import APIRouter

from app.api.alerts import router as alerts_router
from app.api.correlation_analytics import router as correlation_analytics_router
from app.api.devices import router as devices_router
from app.api.incident_correlations import router as incident_correlations_router
from app.api.incidents import router as incidents_router

router = APIRouter()

router.include_router(devices_router)
router.include_router(alerts_router)
router.include_router(incidents_router)
router.include_router(incident_correlations_router)
router.include_router(correlation_analytics_router)
