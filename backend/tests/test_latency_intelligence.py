from app.services.latency_intelligence_service import (
    LatencyIntelligenceService,
)


def test_stable_latency():

    result = (
        LatencyIntelligenceService.analyze(
            [20, 22, 21, 23, 20]
        )
    )

    assert (
        result.latency_stability
        == "STABLE"
    )

    assert (
        result.latency_spike_detected
        is False
    )

def test_degraded_latency():

    result = (
        LatencyIntelligenceService.analyze(
            [20, 40, 60, 50, 25]
        )
    )

    assert (
        result.latency_stability
        == "DEGRADED"
    )

def test_latency_spike_detection():

    result = (
        LatencyIntelligenceService.analyze(
            [25, 26, 24, 28, 220]
        )
    )

    assert (
        result.latency_spike_detected
        is True
    )