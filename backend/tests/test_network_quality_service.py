from app.services.network_quality_service import (
    NetworkQualityService,
)


def test_network_quality():

    result = (
        NetworkQualityService.analyze(
            [
                20,
                21,
                22,
                19,
                20,
                21,
                20,
            ]
        )
    )

    assert result.average_latency > 0
    assert result.p95_latency > 0
    assert result.stability_score > 90

def test_percentile_uses_interpolation():
    result = NetworkQualityService.percentile(
        [10, 20, 30, 40],
        0.95,
    )

    assert result == 38.5