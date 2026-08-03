"""Signal classification and compatibility rules."""

from app.core.correlation import (
    CorrelationSignalFamily,
)
from app.models.alert import AlertType


class CorrelationSignalService:
    """Classify alert types into compatible signal families."""

    _FAMILY_BY_ALERT_TYPE: dict[
        AlertType,
        CorrelationSignalFamily,
    ] = {
        AlertType.GENERIC: (
            CorrelationSignalFamily.GENERIC
        ),
        AlertType.PACKET_LOSS: (
            CorrelationSignalFamily.CONNECTIVITY
        ),
        AlertType.PACKET_LOSS_BURST: (
            CorrelationSignalFamily.CONNECTIVITY
        ),
        AlertType.JITTER: (
            CorrelationSignalFamily.PERFORMANCE
        ),
        AlertType.LATENCY_TREND: (
            CorrelationSignalFamily.PERFORMANCE
        ),
        AlertType.FLAPPING: (
            CorrelationSignalFamily.STABILITY
        ),
        AlertType.PREDICTIVE: (
            CorrelationSignalFamily.PREDICTIVE
        ),
    }

    _COMPATIBLE_FAMILIES: frozenset[
        frozenset[CorrelationSignalFamily]
    ] = frozenset(
        {
            frozenset(
                {
                    CorrelationSignalFamily.CONNECTIVITY,
                    CorrelationSignalFamily.PERFORMANCE,
                }
            ),
            frozenset(
                {
                    CorrelationSignalFamily.CONNECTIVITY,
                    CorrelationSignalFamily.STABILITY,
                }
            ),
            frozenset(
                {
                    CorrelationSignalFamily.PERFORMANCE,
                    CorrelationSignalFamily.EXPERIENCE,
                }
            ),
            frozenset(
                {
                    CorrelationSignalFamily.STABILITY,
                    CorrelationSignalFamily.EXPERIENCE,
                }
            ),
        }
    )

    @classmethod
    def classify(
        cls,
        alert_type: AlertType,
    ) -> CorrelationSignalFamily:
        """Return the stable signal family for an alert type."""

        return cls._FAMILY_BY_ALERT_TYPE.get(
            alert_type,
            CorrelationSignalFamily.GENERIC,
        )

    @classmethod
    def classify_many(
        cls,
        alert_types: frozenset[AlertType],
    ) -> frozenset[CorrelationSignalFamily]:
        """Return all distinct families represented by alert types."""

        return frozenset(
            cls.classify(alert_type)
            for alert_type in alert_types
        )

    @classmethod
    def are_compatible(
        cls,
        source: CorrelationSignalFamily,
        candidate: CorrelationSignalFamily,
    ) -> bool:
        """Return whether two signal families may share a cause."""

        if (
            source == CorrelationSignalFamily.GENERIC
            or candidate
            == CorrelationSignalFamily.GENERIC
        ):
            return False

        if source == candidate:
            return True

        return (
            frozenset(
                {
                    source,
                    candidate,
                }
            )
            in cls._COMPATIBLE_FAMILIES
        )

    @classmethod
    def has_compatible_family(
        cls,
        source: CorrelationSignalFamily,
        candidates: frozenset[
            CorrelationSignalFamily
        ],
    ) -> bool:
        """Return whether any candidate family is compatible."""

        return any(
            cls.are_compatible(
                source,
                candidate,
            )
            for candidate in candidates
        )