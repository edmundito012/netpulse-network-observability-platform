from app.services.network_anomaly_service import (
    NetworkAnomalyService,
)


def test_normal_metric_behavior():

    result = (
        NetworkAnomalyService.analyze(
            values=[
                20,
                21,
                19,
                20,
                21,
                20,
            ],
            metric_name="latency",
        )
    )

    assert result.severity == "NORMAL"
    assert result.anomaly_detected is False


def test_warning_anomaly_detection():

    result = (
        NetworkAnomalyService.analyze(
            values=[
                20,
                21,
                19,
                20,
                21,
                27,
            ],
            metric_name="latency",
        )
    )

    assert result.severity in [
        "WARNING",
        "CRITICAL",
    ]

    assert result.anomaly_detected is True


def test_critical_anomaly_detection():

    result = (
        NetworkAnomalyService.analyze(
            values=[
                20,
                21,
                19,
                20,
                21,
                45,
            ],
            metric_name="latency",
        )
    )

    assert result.severity == "CRITICAL"
    assert result.confidence == "VERY_HIGH"