from app.services.jitter_intelligence_service import (
    JitterIntelligenceService,
)


def test_stable_jitter():

    result = (
        JitterIntelligenceService.analyze(
            [4, 5, 6, 5, 4]
        )
    )

    assert result.jitter_stability == "STABLE"


def test_degraded_jitter():

    result = (
        JitterIntelligenceService.analyze(
            [5, 10, 15, 12, 16]
        )
    )

    assert result.jitter_stability == "DEGRADED"


def test_jitter_spike_detection():

    result = (
        JitterIntelligenceService.analyze(
            [5, 6, 7, 5, 50]
        )
    )

    assert result.jitter_spike_detected is True


def test_jitter_degradation_trend():

    result = (
        JitterIntelligenceService.analyze(
            [5, 10, 15, 20, 25]
        )
    )

    assert result.degradation_detected is True