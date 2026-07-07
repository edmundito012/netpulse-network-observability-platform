from app.services.gaming_experience_service import (
    GamingExperienceService,
)


def test_competitive_gaming_ready():
    result = GamingExperienceService.analyze(
        latency_ms=25,
        jitter_ms=5,
        packet_loss_percent=0,
        latency_spread_ms=10,
        latency_spike_detected=False,
    )

    assert result.competitive_ready is True
    assert result.gaming_score >= 85


def test_rubber_banding_high_risk():
    result = GamingExperienceService.analyze(
        latency_ms=90,
        jitter_ms=35,
        packet_loss_percent=6,
        latency_spread_ms=90,
        latency_spike_detected=True,
    )

    assert result.rubber_banding_risk in [
        "HIGH",
        "CRITICAL",
    ]


def test_poor_hit_registration():
    result = GamingExperienceService.analyze(
        latency_ms=150,
        jitter_ms=45,
        packet_loss_percent=8,
        latency_spread_ms=100,
        latency_spike_detected=True,
    )

    assert result.hit_registration == "POOR"