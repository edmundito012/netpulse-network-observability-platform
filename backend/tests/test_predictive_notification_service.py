from app.services.predictive_notification_service import (
    PredictiveNotificationService,
)


def test_predictive_notification_service():

    result = (
        PredictiveNotificationService
        .send_predictive_alert(
            device_name="VPN Gateway",
            risk_score=85,
            reason="Latency spike detected",
        )
    )

    assert isinstance(
        result,
        bool,
    )