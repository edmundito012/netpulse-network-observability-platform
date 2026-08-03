"""Tests for deterministic correlation configuration."""

import pytest

from app.core.correlation import (
    CorrelationConfiguration,
    CorrelationScoringWeights,
)


def test_default_weights_add_up_to_one() -> None:
    weights = CorrelationScoringWeights()

    total = (
        weights.same_device
        + weights.temporal_proximity
        + weights.signal_compatibility
        + weights.severity_alignment
        + weights.active_incident
        + weights.recent_detection
    )

    assert total == pytest.approx(1.0)


def test_custom_valid_weights_are_allowed() -> None:
    weights = CorrelationScoringWeights(
        same_device=0.40,
        temporal_proximity=0.20,
        signal_compatibility=0.15,
        severity_alignment=0.10,
        active_incident=0.10,
        recent_detection=0.05,
    )

    assert weights.same_device == 0.40


@pytest.mark.parametrize(
    "weights",
    [
        {
            "same_device": -0.10,
            "temporal_proximity": 0.30,
            "signal_compatibility": 0.30,
            "severity_alignment": 0.20,
            "active_incident": 0.20,
            "recent_detection": 0.10,
        },
        {
            "same_device": 0.50,
            "temporal_proximity": 0.20,
            "signal_compatibility": 0.20,
            "severity_alignment": 0.10,
            "active_incident": 0.10,
            "recent_detection": 0.10,
        },
    ],
)
def test_invalid_weights_are_rejected(
    weights: dict[str, float],
) -> None:
    with pytest.raises(ValueError):
        CorrelationScoringWeights(
            **weights
        )


def test_default_configuration() -> None:
    configuration = CorrelationConfiguration()

    assert configuration.window_seconds == 900
    assert configuration.threshold == 0.65
    assert configuration.max_candidates == 25


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
    ),
    [
        (
            "window_seconds",
            59,
        ),
        (
            "window_seconds",
            86_401,
        ),
        (
            "threshold",
            -0.01,
        ),
        (
            "threshold",
            1.01,
        ),
        (
            "max_candidates",
            0,
        ),
        (
            "max_candidates",
            101,
        ),
    ],
)
def test_invalid_configuration_is_rejected(
    field_name: str,
    value: int | float,
) -> None:
    data = {
        "window_seconds": 900,
        "threshold": 0.65,
        "max_candidates": 25,
    }

    data[field_name] = value

    with pytest.raises(ValueError):
        CorrelationConfiguration(
            **data
        )