"""Unit tests for packet loss burst detection."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
)
from app.services.metric_series_service import (
    MetricSeriesSampleResult,
)
from app.services.packet_loss_burst_service import (
    PacketLossBurstService,
)


BASE_TIME = datetime(
    2026,
    7,
    13,
    10,
    0,
    tzinfo=UTC,
)


def build_sample(
    *,
    metric_id: int,
    minute: int,
    value: float | None,
) -> MetricSeriesSampleResult:
    return MetricSeriesSampleResult(
        metric_id=metric_id,
        device_id=1,
        checked_at=(
            BASE_TIME
            + timedelta(minutes=minute)
        ),
        value=value,
    )


def test_detects_completed_warning_burst() -> None:
    samples = [
        build_sample(
            metric_id=1,
            minute=0,
            value=1.0,
        ),
        build_sample(
            metric_id=2,
            minute=1,
            value=8.0,
        ),
        build_sample(
            metric_id=3,
            minute=2,
            value=10.0,
        ),
        build_sample(
            metric_id=4,
            minute=3,
            value=12.0,
        ),
        build_sample(
            metric_id=5,
            minute=4,
            value=2.0,
        ),
    ]

    result = PacketLossBurstService.detect(
        samples=samples,
    )

    assert result.burst_detected is True
    assert result.current_burst_active is False
    assert result.severity == AnalyticsSeverity.WARNING
    assert result.burst_count == 1

    burst = result.bursts[0]

    assert burst.sample_count == 3
    assert burst.peak_packet_loss_percent == 12.0
    assert burst.average_packet_loss_percent == 10.0
    assert burst.duration_seconds == 120.0
    assert burst.status == BurstStatus.COMPLETED


def test_detects_active_critical_burst() -> None:
    samples = [
        build_sample(
            metric_id=1,
            minute=0,
            value=6.0,
        ),
        build_sample(
            metric_id=2,
            minute=1,
            value=15.0,
        ),
        build_sample(
            metric_id=3,
            minute=2,
            value=25.0,
        ),
    ]

    result = PacketLossBurstService.detect(
        samples=samples,
    )

    assert result.burst_detected is True
    assert result.current_burst_active is True
    assert result.severity == AnalyticsSeverity.CRITICAL

    burst = result.bursts[0]

    assert burst.status == BurstStatus.ACTIVE
    assert burst.peak_packet_loss_percent == 25.0


def test_missing_sample_breaks_burst() -> None:
    samples = [
        build_sample(
            metric_id=1,
            minute=0,
            value=10.0,
        ),
        build_sample(
            metric_id=2,
            minute=1,
            value=11.0,
        ),
        build_sample(
            metric_id=3,
            minute=2,
            value=None,
        ),
        build_sample(
            metric_id=4,
            minute=3,
            value=12.0,
        ),
        build_sample(
            metric_id=5,
            minute=4,
            value=13.0,
        ),
    ]

    result = PacketLossBurstService.detect(
        samples=samples,
    )

    assert result.burst_detected is False
    assert result.burst_count == 0
    assert result.missing_samples == 1


def test_large_time_gap_breaks_burst() -> None:
    samples = [
        build_sample(
            metric_id=1,
            minute=0,
            value=10.0,
        ),
        build_sample(
            metric_id=2,
            minute=1,
            value=11.0,
        ),
        build_sample(
            metric_id=3,
            minute=10,
            value=12.0,
        ),
    ]

    result = PacketLossBurstService.detect(
        samples=samples,
        maximum_gap_seconds=120,
    )

    assert result.burst_detected is False


def test_zero_is_preserved_as_real_measurement() -> None:
    samples = [
        build_sample(
            metric_id=1,
            minute=0,
            value=0.0,
        )
    ]

    result = PacketLossBurstService.detect(
        samples=samples,
    )

    assert result.measured_samples == 1
    assert result.missing_samples == 0
    assert result.peak_packet_loss_percent == 0.0
    assert result.average_packet_loss_percent == 0.0


def test_empty_samples_return_normal_result() -> None:
    result = PacketLossBurstService.detect(
        samples=[],
    )

    assert result.burst_detected is False
    assert result.severity == AnalyticsSeverity.NORMAL
    assert result.samples_analyzed == 0
    assert result.peak_packet_loss_percent is None


@pytest.mark.parametrize(
    (
        "warning_threshold",
        "critical_threshold",
        "minimum_samples",
        "maximum_gap",
    ),
    [
        (-1.0, 20.0, 3, 120),
        (5.0, 101.0, 3, 120),
        (20.0, 20.0, 3, 120),
        (5.0, 20.0, 1, 120),
        (5.0, 20.0, 3, 0),
    ],
)
def test_invalid_configuration_is_rejected(
    warning_threshold: float,
    critical_threshold: float,
    minimum_samples: int,
    maximum_gap: int,
) -> None:
    with pytest.raises(ValueError):
        PacketLossBurstService.detect(
            samples=[],
            warning_threshold_percent=(
                warning_threshold
            ),
            critical_threshold_percent=(
                critical_threshold
            ),
            minimum_consecutive_samples=(
                minimum_samples
            ),
            maximum_gap_seconds=maximum_gap,
        )