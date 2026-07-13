"""API tests for packet loss burst analytics."""

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
)
from app.main import app
from app.services.packet_loss_burst_application_service import (
    PacketLossBurstApplicationResult,
)
from app.services.packet_loss_burst_service import (
    PacketLossBurstAnalysisResult,
    PacketLossBurstResult,
)


client = TestClient(app)


@patch(
    "app.api.packet_loss_bursts."
    "PacketLossBurstApplicationService.analyze"
)
def test_packet_loss_burst_endpoint(
    analyze_mock,
) -> None:
    start_at = datetime(
        2026,
        7,
        13,
        10,
        0,
        tzinfo=UTC,
    )
    end_at = datetime(
        2026,
        7,
        13,
        10,
        2,
        tzinfo=UTC,
    )

    analysis = PacketLossBurstAnalysisResult(
        burst_detected=True,
        current_burst_active=True,
        severity=AnalyticsSeverity.WARNING,
        samples_analyzed=3,
        measured_samples=3,
        missing_samples=0,
        burst_count=1,
        longest_burst_samples=3,
        peak_packet_loss_percent=12.0,
        average_packet_loss_percent=10.0,
        warning_threshold_percent=5.0,
        critical_threshold_percent=20.0,
        minimum_consecutive_samples=3,
        maximum_gap_seconds=120,
        bursts=[
            PacketLossBurstResult(
                start_at=start_at,
                end_at=end_at,
                duration_seconds=120.0,
                sample_count=3,
                average_packet_loss_percent=10.0,
                peak_packet_loss_percent=12.0,
                severity=AnalyticsSeverity.WARNING,
                status=BurstStatus.ACTIVE,
            )
        ],
    )

    analyze_mock.return_value = (
        PacketLossBurstApplicationResult(
            device_id=7,
            series=None,
            analysis=analysis,
        )
    )

    response = client.get(
        "/analytics/packet-loss-bursts",
        params={
            "device_id": 7,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["device_id"] == 7
    assert payload["burst_detected"] is True
    assert payload["current_burst_active"] is True
    assert payload["severity"] == "WARNING"
    assert payload["burst_count"] == 1
    assert payload["bursts"][0]["sample_count"] == 3


def test_packet_loss_burst_endpoint_rejects_bad_thresholds() -> None:
    response = client.get(
        "/analytics/packet-loss-bursts",
        params={
            "warning_threshold_percent": 30,
            "critical_threshold_percent": 20,
        },
    )

    assert response.status_code == 422


def test_packet_loss_burst_endpoint_rejects_small_window() -> None:
    response = client.get(
        "/analytics/packet-loss-bursts",
        params={
            "limit": 1,
        },
    )

    assert response.status_code == 422