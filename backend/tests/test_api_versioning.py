"""Tests for versioned API route registration."""

from app.main import app


def get_openapi_paths() -> set[str]:
    """Return every path registered in the OpenAPI schema."""

    return set(app.openapi()["paths"])


def test_v1_operational_routes_are_registered():
    paths = get_openapi_paths()

    expected_paths = {
        "/api/v1/devices/",
        "/api/v1/alerts/",
        "/api/v1/incidents",
        "/api/v1/incident-correlations",
        "/api/v1/analytics/correlations",
    }

    assert expected_paths.issubset(paths)


def test_legacy_routes_remain_registered():
    paths = get_openapi_paths()

    expected_paths = {
        "/devices/",
        "/alerts/",
        "/incidents",
        "/incident-correlations",
        "/analytics/correlations",
    }

    assert expected_paths.issubset(paths)


def test_operational_endpoints_remain_unversioned():
    paths = get_openapi_paths()

    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/health/startup" in paths
    assert "/health" in paths
    assert "/metrics" in paths

    assert "/api/v1/health/live" not in paths
    assert "/api/v1/health/ready" not in paths
    assert "/api/v1/metrics" not in paths
