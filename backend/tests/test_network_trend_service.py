from app.services.network_trend_service import (
    NetworkTrendService,
)


def test_increasing_trend():

    result = (
        NetworkTrendService.analyze(
            [18, 20, 22, 24, 26, 28, 30]
        )
    )

    assert result.trend == "INCREASING"
    assert result.slope > 0
    assert result.predicted_next_latency > 30


def test_decreasing_trend():

    result = (
        NetworkTrendService.analyze(
            [40, 38, 36, 34, 32, 30]
        )
    )

    assert result.trend == "DECREASING"
    assert result.slope < 0


def test_stable_trend():

    result = (
        NetworkTrendService.analyze(
            [20, 20, 21, 20, 20, 21]
        )
    )

    assert result.trend == "STABLE"
    assert result.risk == "LOW"


def test_high_volatility():

    result = (
        NetworkTrendService.analyze(
            [20, 22, 80, 21, 23, 90]
        )
    )

    assert result.volatility == "HIGH"
    assert result.risk == "HIGH"