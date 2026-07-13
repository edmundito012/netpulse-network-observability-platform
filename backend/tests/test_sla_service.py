from app.services.sla_service import (
    SLAService,
)


def test_sla_passes_with_healthy_metrics():
    result = SLAService.calculate(
        statuses=[
            "ONLINE",
            "ONLINE",
            "ONLINE",
            "ONLINE",
        ],
        latencies_ms=[
            20,
            25,
            30,
            22,
        ],
        packet_losses_percent=[
            0,
            0,
            0.2,
            0,
        ],
        jitters_ms=[
            4,
            5,
            6,
            5,
        ],
    )

    assert result.status == "PASS"
    assert result.overall_compliance_percent == 100
    assert result.breached_metrics == []


def test_sla_detects_breach():
    result = SLAService.calculate(
        statuses=[
            "ONLINE",
            "OFFLINE",
            "ONLINE",
            "OFFLINE",
        ],
        latencies_ms=[
            40,
            150,
            180,
            200,
        ],
        packet_losses_percent=[
            0,
            3,
            5,
            8,
        ],
        jitters_ms=[
            10,
            35,
            50,
            60,
        ],
    )

    assert result.status == "BREACH"
    assert "availability" in result.breached_metrics
    assert "latency" in result.breached_metrics
    assert "packet_loss" in result.breached_metrics
    assert "jitter" in result.breached_metrics


def test_sla_returns_unknown_without_metrics():
    result = SLAService.calculate(
        statuses=[],
        latencies_ms=[],
        packet_losses_percent=[],
        jitters_ms=[],
    )

    assert result.status == "UNKNOWN"
    assert result.samples_analyzed == 0