from app.models.alert import AlertSeverity
from app.services.jitter_alert_service import JitterAlertService


def test_returns_none_below_warning_threshold():
    result = JitterAlertService.evaluate(
        device_name="router-01",
        jitter_ms=39.99,
    )

    assert result is None


def test_returns_warning_at_warning_threshold():
    result = JitterAlertService.evaluate(
        device_name="router-01",
        jitter_ms=40.0,
    )

    assert result == (
        AlertSeverity.WARNING,
        "High jitter detected on router-01: 40.00 ms",
    )


def test_returns_warning_below_critical_threshold():
    result = JitterAlertService.evaluate(
        device_name="router-01",
        jitter_ms=59.99,
    )

    assert result == (
        AlertSeverity.WARNING,
        "High jitter detected on router-01: 59.99 ms",
    )


def test_returns_critical_at_critical_threshold():
    result = JitterAlertService.evaluate(
        device_name="router-01",
        jitter_ms=60.0,
    )

    assert result == (
        AlertSeverity.CRITICAL,
        "Critical jitter detected on router-01: 60.00 ms",
    )
