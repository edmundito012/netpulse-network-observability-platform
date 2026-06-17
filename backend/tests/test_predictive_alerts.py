from types import SimpleNamespace

from app.services.predictive_alert_service import (
    PredictiveAlertService,
)


def test_detect_latency_trend():

    metrics = [
        SimpleNamespace(response_time_ms=10),
        SimpleNamespace(response_time_ms=20),
        SimpleNamespace(response_time_ms=30),
        SimpleNamespace(response_time_ms=40),
        SimpleNamespace(response_time_ms=50),
    ]

    assert (
        PredictiveAlertService.detect_latency_trend(
            metrics
        )
        is True
    )


def test_detect_packet_loss_trend():

    metrics = [
        SimpleNamespace(packet_loss_percent=1),
        SimpleNamespace(packet_loss_percent=2),
        SimpleNamespace(packet_loss_percent=3),
        SimpleNamespace(packet_loss_percent=4),
        SimpleNamespace(packet_loss_percent=5),
    ]

    assert (
        PredictiveAlertService.detect_packet_loss_trend(
            metrics
        )
        is True
    )


def test_detect_jitter_trend():

    metrics = [
        SimpleNamespace(jitter_ms=5),
        SimpleNamespace(jitter_ms=10),
        SimpleNamespace(jitter_ms=15),
        SimpleNamespace(jitter_ms=20),
        SimpleNamespace(jitter_ms=25),
    ]

    assert (
        PredictiveAlertService.detect_jitter_trend(
            metrics
        )
        is True
    )