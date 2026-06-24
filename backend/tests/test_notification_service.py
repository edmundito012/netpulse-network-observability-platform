from app.services.notification_service import (
    NotificationService,
)


def test_build_predictive_alert():

    result = (
        NotificationService
        .build_predictive_alert_message(
            device_name="Google DNS",
            risk_score=85,
            reason="Latency spike detected",
        )
    )

    assert result.title == "Predictive Alert"

    assert "Google DNS" in result.body


def test_build_network_risk_alert():

    result = (
        NotificationService
        .build_network_risk_message(
            risk_score=80,
            risk_level="HIGH",
        )
    )

    assert result.title == (
        "Network Risk Alert"
    )

    assert "HIGH" in result.body