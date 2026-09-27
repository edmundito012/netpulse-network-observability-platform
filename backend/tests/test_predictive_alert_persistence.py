from unittest.mock import Mock

import pytest

from app.models.alert import AlertSeverity
from app.services import predictive_alert_persistence_service
from app.services.predictive_alert_persistence_service import (
    PredictiveAlertPersistenceService,
)


@pytest.mark.parametrize(
    ("service_method", "builder_method"),
    [
        ("create_latency_alert", "build_latency_alert"),
        ("create_packet_loss_alert", "build_packet_loss_alert"),
        ("create_jitter_alert", "build_jitter_alert"),
    ],
)
def test_returns_existing_active_alert(
    monkeypatch,
    service_method,
    builder_method,
):
    db = object()
    active_alert = object()
    get_active_alert = Mock(return_value=active_alert)
    create = Mock()
    build_payload = Mock()

    monkeypatch.setattr(
        predictive_alert_persistence_service.AlertRepository,
        "get_active_alert_for_device",
        get_active_alert,
    )
    monkeypatch.setattr(
        predictive_alert_persistence_service.AlertRepository,
        "create",
        create,
    )
    monkeypatch.setattr(
        predictive_alert_persistence_service.PredictiveAlertGenerationService,
        builder_method,
        build_payload,
    )

    result = getattr(
        PredictiveAlertPersistenceService,
        service_method,
    )(
        db=db,
        device_id=10,
    )

    assert result is active_alert
    get_active_alert.assert_called_once_with(
        db=db,
        device_id=10,
    )
    build_payload.assert_not_called()
    create.assert_not_called()


@pytest.mark.parametrize(
    ("service_method", "builder_method", "severity", "message"),
    [
        (
            "create_latency_alert",
            "build_latency_alert",
            AlertSeverity.WARNING,
            "Predicted latency degradation",
        ),
        (
            "create_packet_loss_alert",
            "build_packet_loss_alert",
            AlertSeverity.CRITICAL,
            "Predicted packet loss degradation",
        ),
        (
            "create_jitter_alert",
            "build_jitter_alert",
            AlertSeverity.WARNING,
            "Predicted jitter degradation",
        ),
    ],
)
def test_builds_and_persists_new_alert(
    monkeypatch,
    service_method,
    builder_method,
    severity,
    message,
):
    db = object()
    created_alert = object()
    get_active_alert = Mock(return_value=None)
    build_payload = Mock(
        return_value={
            "severity": severity,
            "message": message,
        }
    )
    create = Mock(return_value=created_alert)

    monkeypatch.setattr(
        predictive_alert_persistence_service.AlertRepository,
        "get_active_alert_for_device",
        get_active_alert,
    )
    monkeypatch.setattr(
        predictive_alert_persistence_service.PredictiveAlertGenerationService,
        builder_method,
        build_payload,
    )
    monkeypatch.setattr(
        predictive_alert_persistence_service.AlertRepository,
        "create",
        create,
    )

    result = getattr(
        PredictiveAlertPersistenceService,
        service_method,
    )(
        db=db,
        device_id=20,
    )

    assert result is created_alert
    get_active_alert.assert_called_once_with(
        db=db,
        device_id=20,
    )
    build_payload.assert_called_once_with()
    create.assert_called_once_with(
        db=db,
        device_id=20,
        severity=severity,
        message=message,
    )
