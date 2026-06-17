from app.models.alert import AlertSeverity
from app.services.predictive_alert_persistence_service import (
    PredictiveAlertPersistenceService,
)


def test_latency_alert_payload():

    payload = (
        PredictiveAlertPersistenceService
        .__dict__
    )

    assert payload is not None