"""Application-level FastAPI router registry."""

from fastapi import APIRouter

from app.api.alerts import router as alerts_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.business_impact import router as business_impact_router
from app.api.correlation_analytics import router as correlation_analytics_router
from app.api.dashboard import router as dashboard_router
from app.api.device_risk import router as device_risk_router
from app.api.device_state import router as device_state_router
from app.api.devices import router as devices_router
from app.api.events import router as events_router
from app.api.experience_summary import router as experience_summary_router
from app.api.gaming_experience import router as gaming_experience_router
from app.api.gaming_impact import router as gaming_impact_router
from app.api.incident_correlations import router as incident_correlations_router
from app.api.incident_timeline import router as incident_timeline_router
from app.api.incidents import router as incidents_router
from app.api.metric_series import router as metric_series_router
from app.api.network_anomalies import router as network_anomalies_router
from app.api.network_health_score import router as network_health_score_router
from app.api.network_impact import router as network_impact_router
from app.api.network_quality import router as network_quality_router
from app.api.network_risk import router as network_risk_router
from app.api.network_trends import router as network_trends_router
from app.api.notifications import router as notifications_router
from app.api.packet_loss_bursts import router as packet_loss_bursts_router
from app.api.portfolio_correlations import router as portfolio_correlations_router
from app.api.portfolio_dashboard import router as portfolio_dashboard_router
from app.api.portfolio_incidents import router as portfolio_incidents_router
from app.api.sla import router as sla_router
from app.api.streaming_experience import router as streaming_experience_router
from app.api.users import router as users_router
from app.api.video_call_experience import router as video_call_router
from app.api.websocket import router as websocket_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(audit_logs_router)
router.include_router(devices_router)
router.include_router(alerts_router)
router.include_router(events_router)
router.include_router(dashboard_router)
router.include_router(websocket_router)
router.include_router(device_state_router)
router.include_router(network_impact_router)
router.include_router(business_impact_router)
router.include_router(gaming_impact_router)
router.include_router(network_risk_router)
router.include_router(device_risk_router)
router.include_router(notifications_router)
router.include_router(gaming_experience_router)
router.include_router(streaming_experience_router)
router.include_router(experience_summary_router)
router.include_router(network_quality_router)
router.include_router(video_call_router)
router.include_router(network_trends_router)
router.include_router(network_anomalies_router)
router.include_router(network_health_score_router)
router.include_router(sla_router)
router.include_router(metric_series_router)
router.include_router(packet_loss_bursts_router)
router.include_router(incidents_router)
router.include_router(incident_correlations_router)
router.include_router(portfolio_correlations_router)
router.include_router(correlation_analytics_router)
router.include_router(incident_timeline_router)
router.include_router(portfolio_dashboard_router)
router.include_router(portfolio_incidents_router)
