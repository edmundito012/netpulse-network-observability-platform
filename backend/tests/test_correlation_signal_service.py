"""Tests for signal-family classification."""

import pytest

from app.core.correlation import (
    CorrelationSignalFamily,
)
from app.models.alert import AlertType
from app.services.correlation_signal_service import (
    CorrelationSignalService,
)


@pytest.mark.parametrize(
    (
        "alert_type",
        "expected_family",
    ),
    [
        (
            AlertType.GENERIC,
            CorrelationSignalFamily.GENERIC,
        ),
        (
            AlertType.PACKET_LOSS,
            CorrelationSignalFamily.CONNECTIVITY,
        ),
        (
            AlertType.PACKET_LOSS_BURST,
            CorrelationSignalFamily.CONNECTIVITY,
        ),
        (
            AlertType.JITTER,
            CorrelationSignalFamily.PERFORMANCE,
        ),
        (
            AlertType.LATENCY_TREND,
            CorrelationSignalFamily.PERFORMANCE,
        ),
        (
            AlertType.FLAPPING,
            CorrelationSignalFamily.STABILITY,
        ),
        (
            AlertType.PREDICTIVE,
            CorrelationSignalFamily.PREDICTIVE,
        ),
    ],
)
def test_classify_alert_type(
    alert_type: AlertType,
    expected_family: CorrelationSignalFamily,
) -> None:
    assert (
        CorrelationSignalService.classify(
            alert_type
        )
        == expected_family
    )


def test_classify_many_removes_duplicates() -> None:
    result = (
        CorrelationSignalService.classify_many(
            frozenset(
                {
                    AlertType.PACKET_LOSS,
                    AlertType.PACKET_LOSS_BURST,
                    AlertType.JITTER,
                }
            )
        )
    )

    assert result == frozenset(
        {
            CorrelationSignalFamily.CONNECTIVITY,
            CorrelationSignalFamily.PERFORMANCE,
        }
    )


@pytest.mark.parametrize(
    (
        "source",
        "candidate",
    ),
    [
        (
            CorrelationSignalFamily.CONNECTIVITY,
            CorrelationSignalFamily.CONNECTIVITY,
        ),
        (
            CorrelationSignalFamily.CONNECTIVITY,
            CorrelationSignalFamily.PERFORMANCE,
        ),
        (
            CorrelationSignalFamily.CONNECTIVITY,
            CorrelationSignalFamily.STABILITY,
        ),
        (
            CorrelationSignalFamily.PERFORMANCE,
            CorrelationSignalFamily.EXPERIENCE,
        ),
        (
            CorrelationSignalFamily.STABILITY,
            CorrelationSignalFamily.EXPERIENCE,
        ),
    ],
)
def test_compatible_signal_families(
    source: CorrelationSignalFamily,
    candidate: CorrelationSignalFamily,
) -> None:
    assert (
        CorrelationSignalService.are_compatible(
            source,
            candidate,
        )
        is True
    )

    assert (
        CorrelationSignalService.are_compatible(
            candidate,
            source,
        )
        is True
    )


@pytest.mark.parametrize(
    (
        "source",
        "candidate",
    ),
    [
        (
            CorrelationSignalFamily.PREDICTIVE,
            CorrelationSignalFamily.STABILITY,
        ),
        (
            CorrelationSignalFamily.PREDICTIVE,
            CorrelationSignalFamily.PERFORMANCE,
        ),
        (
            CorrelationSignalFamily.GENERIC,
            CorrelationSignalFamily.CONNECTIVITY,
        ),
        (
            CorrelationSignalFamily.GENERIC,
            CorrelationSignalFamily.GENERIC,
        ),
    ],
)
def test_incompatible_signal_families(
    source: CorrelationSignalFamily,
    candidate: CorrelationSignalFamily,
) -> None:
    expected = (
        source == candidate
        and source
        != CorrelationSignalFamily.GENERIC
    )

    assert (
        CorrelationSignalService.are_compatible(
            source,
            candidate,
        )
        is expected
    )


def test_has_compatible_candidate_family() -> None:
    result = (
        CorrelationSignalService
        .has_compatible_family(
            CorrelationSignalFamily.CONNECTIVITY,
            frozenset(
                {
                    CorrelationSignalFamily.PREDICTIVE,
                    CorrelationSignalFamily.PERFORMANCE,
                }
            ),
        )
    )

    assert result is True


def test_has_no_compatible_candidate_family() -> None:
    result = (
        CorrelationSignalService
        .has_compatible_family(
            CorrelationSignalFamily.PREDICTIVE,
            frozenset(
                {
                    CorrelationSignalFamily.STABILITY,
                    CorrelationSignalFamily.PERFORMANCE,
                }
            ),
        )
    )

    assert result is False