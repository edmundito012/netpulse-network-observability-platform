from app.services.network_health_score_service import (
    NetworkHealthScoreService,
)


def test_network_health():

    result = (
        NetworkHealthScoreService.analyze(
            latency_score=95,
            jitter_score=90,
            packet_loss_score=100,
            stability_score=95,
        )
    )

    assert result.health_score >= 90
    assert result.grade == "A+"