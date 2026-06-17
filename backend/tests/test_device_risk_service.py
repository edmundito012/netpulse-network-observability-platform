from app.services.device_risk_service import DeviceRiskService


def test_classify_high_device_risk():
    risk_level = DeviceRiskService.classify_risk_level(90)

    assert risk_level == "HIGH"


def test_classify_medium_device_risk():
    risk_level = DeviceRiskService.classify_risk_level(60)

    assert risk_level == "MEDIUM"


def test_classify_low_device_risk():
    risk_level = DeviceRiskService.classify_risk_level(20)

    assert risk_level == "LOW"