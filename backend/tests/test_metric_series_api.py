"""API tests for temporal metric series."""

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.analytics import (
    MetricName,
    MissingValuePolicy,
    SortDirection,
)
from app.main import app
from app.services.metric_series_service import (
    MetricSeriesResult,
    MetricSeriesSampleResult,
)


client = TestClient(app)


@patch(
    "app.api.metric_series."
    "MetricSeriesService.get_series"
)
def test_get_metric_series_returns_temporal_samples(
    get_series_mock,
) -> None:
    checked_at = datetime(
        2026,
        7,
        13,
        12,
        0,
        tzinfo=UTC,
    )

    get_series_mock.return_value = MetricSeriesResult(
        device_id=7,
        metric_name=MetricName.LATENCY,
        start_at=None,
        end_at=None,
        requested_limit=100,
        sort_direction=SortDirection.ASCENDING,
        missing_value_policy=MissingValuePolicy.DROP,
        database_sample_count=2,
        returned_sample_count=1,
        missing_sample_count=1,
        samples=[
            MetricSeriesSampleResult(
                metric_id=20,
                device_id=7,
                checked_at=checked_at,
                value=14.5,
            )
        ],
    )

    response = client.get(
        "/analytics/metric-series",
        params={
            "device_id": 7,
            "metric_name": "latency",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["device_id"] == 7
    assert payload["metric_name"] == "latency"
    assert payload["database_sample_count"] == 2
    assert payload["returned_sample_count"] == 1
    assert payload["missing_sample_count"] == 1
    assert payload["samples"][0]["value"] == 14.5


def test_get_metric_series_rejects_invalid_device_id() -> None:
    response = client.get(
        "/analytics/metric-series",
        params={
            "device_id": 0,
        },
    )

    assert response.status_code == 422


def test_get_metric_series_rejects_unknown_metric() -> None:
    response = client.get(
        "/analytics/metric-series",
        params={
            "device_id": 7,
            "metric_name": "cpu_temperature",
        },
    )

    assert response.status_code == 422