"""Prometheus metrics exposed by NetPulse."""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "netpulse_http_requests_total",
    "Total HTTP requests",
    [
        "method",
        "endpoint",
        "status",
    ],
)


http_request_duration_seconds = Histogram(
    "netpulse_http_request_duration_seconds",
    "HTTP request duration in seconds",
    [
        "method",
        "endpoint",
    ],
)


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

active_websocket_connections = Gauge(
    "netpulse_active_websocket_connections",
    "Active websocket connections",
    [
        "channel",
    ],
)


# ---------------------------------------------------------------------------
# Devices and alerts
# ---------------------------------------------------------------------------

device_status_total = Gauge(
    "netpulse_device_status_total",
    "Device count grouped by operational status",
    [
        "status",
    ],
)


active_alerts_total = Gauge(
    "netpulse_active_alerts_total",
    "Current number of active alerts",
)


# ---------------------------------------------------------------------------
# Correlation Engine
# ---------------------------------------------------------------------------

correlation_worker_runs_total = Counter(
    "netpulse_correlation_worker_runs_total",
    "Total correlation worker executions",
    [
        "status",
    ],
)


correlation_worker_duration_seconds = Histogram(
    "netpulse_correlation_worker_duration_seconds",
    "Duration of correlation worker executions in seconds",
    buckets=(
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ),
)


correlation_worker_pending_alerts = Gauge(
    "netpulse_correlation_worker_pending_alerts",
    (
        "Number of pending alerts discovered at the beginning "
        "of the latest correlation worker execution"
    ),
)


correlation_worker_processed_alerts_total = Counter(
    "netpulse_correlation_worker_processed_alerts_total",
    "Total alerts processed by the correlation worker",
    [
        "status",
    ],
)


correlation_evaluations_total = Counter(
    "netpulse_correlation_evaluations_total",
    "Total successful correlation evaluations",
    [
        "outcome",
    ],
)


correlation_applications_total = Counter(
    "netpulse_correlation_applications_total",
    "Total correlation decisions handled by application status",
    [
        "status",
    ],
)


correlation_failures_total = Counter(
    "netpulse_correlation_failures_total",
    "Total correlation processing failures",
    [
        "exception_type",
    ],
)


correlation_incidents_created_total = Counter(
    "netpulse_correlation_incidents_created_total",
    "Total incidents created automatically by the Correlation Engine",
)


correlation_existing_incidents_matched_total = Counter(
    "netpulse_correlation_existing_incidents_matched_total",
    "Total alerts matched to an existing incident",
)


correlation_no_action_total = Counter(
    "netpulse_correlation_no_action_total",
    "Total correlation evaluations resulting in no action",
)