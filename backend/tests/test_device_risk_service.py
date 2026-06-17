from app.services.device_risk_service import (
    DeviceRiskService,
)


def test_high_device_risk():

    result = (
        DeviceRiskService
        .calculate_device_risk(
            device_id=1,
            device_name="Router",
            health_score=30,
            failure_risk=90,
        )
    )

    assert result.risk_level == "HIGH"


def test_low_device_risk():

    result = (
        DeviceRiskService
        .calculate_device_risk(
            device_id=1,
            device_name="Router",
            health_score=95,
            failure_risk=5,
        )
    )

    assert result.risk_level == "LOW"