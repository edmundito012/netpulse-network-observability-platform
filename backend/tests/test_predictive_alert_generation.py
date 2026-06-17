from app.models.alert import AlertSeverity

from app.services.predictive_alert_generation_service import (
    PredictiveAlertGenerationService,
)


def test_latency_alert_generation():

    alert = (
        PredictiveAlertGenerationService
        .build_latency_alert()
    )

    assert (
        alert["severity"]
        == AlertSeverity.WARNING
    )

    assert (
        "Latency trend"
        in alert["message"]
    )


def test_packet_loss_alert_generation():

    alert = (
        PredictiveAlertGenerationService
        .build_packet_loss_alert()
    )

    assert (
        alert["severity"]
        == AlertSeverity.WARNING
    )

    assert (
        "Packet loss trend"
        in alert["message"]
    )


def test_jitter_alert_generation():

    alert = (
        PredictiveAlertGenerationService
        .build_jitter_alert()
    )

    assert (
        alert["severity"]
        == AlertSeverity.WARNING
    )

    assert (
        "Jitter trend"
        in alert["message"]
    )