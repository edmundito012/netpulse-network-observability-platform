from prometheus_client import Counter, Gauge, Histogram


http_requests_total = Counter(
    "netpulse_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)


http_request_duration_seconds = Histogram(
    "netpulse_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)


active_websocket_connections = Gauge(
    "netpulse_active_websocket_connections",
    "Active websocket connections",
    ["channel"],
)


device_status_total = Gauge(
    "netpulse_device_status_total",
    "Device status count",
    ["status"],
)


active_alerts_total = Gauge(
    "netpulse_active_alerts_total",
    "Active alerts count",
)