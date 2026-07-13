"""Packet loss burst detection domain service."""

from dataclasses import dataclass
from datetime import datetime
from statistics import mean

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
)
from app.services.metric_series_service import (
    MetricSeriesSampleResult,
)


@dataclass(frozen=True, slots=True)
class PacketLossBurstResult:
    """One sustained packet loss degradation period."""

    start_at: datetime
    end_at: datetime

    duration_seconds: float
    sample_count: int

    average_packet_loss_percent: float
    peak_packet_loss_percent: float

    severity: AnalyticsSeverity
    status: BurstStatus


@dataclass(frozen=True, slots=True)
class PacketLossBurstAnalysisResult:
    """Complete packet loss burst analysis for one metric window."""

    burst_detected: bool
    current_burst_active: bool

    severity: AnalyticsSeverity

    samples_analyzed: int
    measured_samples: int
    missing_samples: int

    burst_count: int
    longest_burst_samples: int

    peak_packet_loss_percent: float | None
    average_packet_loss_percent: float | None

    warning_threshold_percent: float
    critical_threshold_percent: float
    minimum_consecutive_samples: int
    maximum_gap_seconds: int

    bursts: list[PacketLossBurstResult]


class PacketLossBurstService:
    """Detect sustained packet loss degradation in chronological samples."""

    DEFAULT_WARNING_THRESHOLD_PERCENT = 5.0
    DEFAULT_CRITICAL_THRESHOLD_PERCENT = 20.0
    DEFAULT_MINIMUM_CONSECUTIVE_SAMPLES = 3
    DEFAULT_MAXIMUM_GAP_SECONDS = 120

    @classmethod
    def detect(
        cls,
        *,
        samples: list[MetricSeriesSampleResult],
        warning_threshold_percent: float = (
            DEFAULT_WARNING_THRESHOLD_PERCENT
        ),
        critical_threshold_percent: float = (
            DEFAULT_CRITICAL_THRESHOLD_PERCENT
        ),
        minimum_consecutive_samples: int = (
            DEFAULT_MINIMUM_CONSECUTIVE_SAMPLES
        ),
        maximum_gap_seconds: int = (
            DEFAULT_MAXIMUM_GAP_SECONDS
        ),
    ) -> PacketLossBurstAnalysisResult:
        """Detect consecutive packet loss samples above a threshold.

        A missing value, a value below the warning threshold, or a
        temporal gap larger than ``maximum_gap_seconds`` terminates the
        current candidate burst.
        """

        cls._validate_configuration(
            warning_threshold_percent=(
                warning_threshold_percent
            ),
            critical_threshold_percent=(
                critical_threshold_percent
            ),
            minimum_consecutive_samples=(
                minimum_consecutive_samples
            ),
            maximum_gap_seconds=maximum_gap_seconds,
        )

        ordered_samples = sorted(
            samples,
            key=lambda sample: (
                sample.checked_at,
                sample.metric_id,
            ),
        )

        bursts: list[PacketLossBurstResult] = []
        candidate: list[MetricSeriesSampleResult] = []

        measured_values: list[float] = []
        missing_samples = 0

        for sample in ordered_samples:
            if sample.value is None:
                missing_samples += 1

                cls._complete_candidate(
                    candidate=candidate,
                    bursts=bursts,
                    minimum_consecutive_samples=(
                        minimum_consecutive_samples
                    ),
                    critical_threshold_percent=(
                        critical_threshold_percent
                    ),
                    active=False,
                )

                candidate = []
                continue

            value = float(sample.value)
            measured_values.append(value)

            if value < warning_threshold_percent:
                cls._complete_candidate(
                    candidate=candidate,
                    bursts=bursts,
                    minimum_consecutive_samples=(
                        minimum_consecutive_samples
                    ),
                    critical_threshold_percent=(
                        critical_threshold_percent
                    ),
                    active=False,
                )

                candidate = []
                continue

            if candidate:
                previous_sample = candidate[-1]

                gap_seconds = (
                    sample.checked_at
                    - previous_sample.checked_at
                ).total_seconds()

                if gap_seconds > maximum_gap_seconds:
                    cls._complete_candidate(
                        candidate=candidate,
                        bursts=bursts,
                        minimum_consecutive_samples=(
                            minimum_consecutive_samples
                        ),
                        critical_threshold_percent=(
                            critical_threshold_percent
                        ),
                        active=False,
                    )

                    candidate = []

            candidate.append(sample)

        cls._complete_candidate(
            candidate=candidate,
            bursts=bursts,
            minimum_consecutive_samples=(
                minimum_consecutive_samples
            ),
            critical_threshold_percent=(
                critical_threshold_percent
            ),
            active=True,
        )

        overall_severity = cls._overall_severity(
            bursts,
        )

        return PacketLossBurstAnalysisResult(
            burst_detected=bool(bursts),
            current_burst_active=any(
                burst.status == BurstStatus.ACTIVE
                for burst in bursts
            ),
            severity=overall_severity,
            samples_analyzed=len(ordered_samples),
            measured_samples=len(measured_values),
            missing_samples=missing_samples,
            burst_count=len(bursts),
            longest_burst_samples=max(
                (
                    burst.sample_count
                    for burst in bursts
                ),
                default=0,
            ),
            peak_packet_loss_percent=cls._optional_round(
                max(measured_values)
                if measured_values
                else None
            ),
            average_packet_loss_percent=cls._optional_round(
                mean(measured_values)
                if measured_values
                else None
            ),
            warning_threshold_percent=(
                warning_threshold_percent
            ),
            critical_threshold_percent=(
                critical_threshold_percent
            ),
            minimum_consecutive_samples=(
                minimum_consecutive_samples
            ),
            maximum_gap_seconds=maximum_gap_seconds,
            bursts=bursts,
        )

    @classmethod
    def _complete_candidate(
        cls,
        *,
        candidate: list[MetricSeriesSampleResult],
        bursts: list[PacketLossBurstResult],
        minimum_consecutive_samples: int,
        critical_threshold_percent: float,
        active: bool,
    ) -> None:
        if len(candidate) < minimum_consecutive_samples:
            return

        values = [
            float(sample.value)
            for sample in candidate
            if sample.value is not None
        ]

        if not values:
            return

        peak = max(values)

        severity = (
            AnalyticsSeverity.CRITICAL
            if peak >= critical_threshold_percent
            else AnalyticsSeverity.WARNING
        )

        start_at = candidate[0].checked_at
        end_at = candidate[-1].checked_at

        bursts.append(
            PacketLossBurstResult(
                start_at=start_at,
                end_at=end_at,
                duration_seconds=round(
                    max(
                        0.0,
                        (
                            end_at
                            - start_at
                        ).total_seconds(),
                    ),
                    2,
                ),
                sample_count=len(candidate),
                average_packet_loss_percent=round(
                    mean(values),
                    2,
                ),
                peak_packet_loss_percent=round(
                    peak,
                    2,
                ),
                severity=severity,
                status=(
                    BurstStatus.ACTIVE
                    if active
                    else BurstStatus.COMPLETED
                ),
            )
        )

    @staticmethod
    def _overall_severity(
        bursts: list[PacketLossBurstResult],
    ) -> AnalyticsSeverity:
        if any(
            burst.severity
            == AnalyticsSeverity.CRITICAL
            for burst in bursts
        ):
            return AnalyticsSeverity.CRITICAL

        if bursts:
            return AnalyticsSeverity.WARNING

        return AnalyticsSeverity.NORMAL

    @staticmethod
    def _optional_round(
        value: float | None,
    ) -> float | None:
        if value is None:
            return None

        return round(
            float(value),
            2,
        )

    @staticmethod
    def _validate_configuration(
        *,
        warning_threshold_percent: float,
        critical_threshold_percent: float,
        minimum_consecutive_samples: int,
        maximum_gap_seconds: int,
    ) -> None:
        if not 0 <= warning_threshold_percent <= 100:
            raise ValueError(
                "warning_threshold_percent must be "
                "between 0 and 100"
            )

        if not 0 <= critical_threshold_percent <= 100:
            raise ValueError(
                "critical_threshold_percent must be "
                "between 0 and 100"
            )

        if (
            critical_threshold_percent
            <= warning_threshold_percent
        ):
            raise ValueError(
                "critical_threshold_percent must be greater "
                "than warning_threshold_percent"
            )

        if minimum_consecutive_samples < 2:
            raise ValueError(
                "minimum_consecutive_samples must be "
                "greater than or equal to 2"
            )

        if maximum_gap_seconds < 1:
            raise ValueError(
                "maximum_gap_seconds must be greater "
                "than or equal to 1"
            )