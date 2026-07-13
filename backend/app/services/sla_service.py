from dataclasses import dataclass


@dataclass(frozen=True)
class SLAThresholds:
    latency_ms: float = 100
    packet_loss_percent: float = 1
    jitter_ms: float = 30

    pass_compliance_percent: float = 99
    warning_compliance_percent: float = 95


@dataclass
class SLAResult:
    samples_analyzed: int

    availability_percent: float
    latency_compliance_percent: float
    packet_loss_compliance_percent: float
    jitter_compliance_percent: float

    overall_compliance_percent: float

    status: str
    breached_metrics: list[str]
    recommendation: str


class SLAService:

    @staticmethod
    def calculate_compliance(
        values: list[float],
        maximum_allowed: float,
    ) -> float:
        if not values:
            return 0

        compliant_samples = sum(
            value <= maximum_allowed
            for value in values
        )

        return round(
            compliant_samples / len(values) * 100,
            2,
        )

    @staticmethod
    def calculate_availability(
        statuses: list[str],
    ) -> float:
        if not statuses:
            return 0

        online_samples = sum(
            status.upper() == "ONLINE"
            for status in statuses
        )

        return round(
            online_samples / len(statuses) * 100,
            2,
        )

    @staticmethod
    def classify_status(
        compliance: float,
        samples_analyzed: int,
        thresholds: SLAThresholds,
    ) -> str:
        if samples_analyzed == 0:
            return "UNKNOWN"

        if compliance >= thresholds.pass_compliance_percent:
            return "PASS"

        if compliance >= thresholds.warning_compliance_percent:
            return "WARNING"

        return "BREACH"

    @staticmethod
    def build_recommendation(
        status: str,
        breached_metrics: list[str],
    ) -> str:
        if status == "UNKNOWN":
            return (
                "No network metrics are available. "
                "Run monitoring checks before evaluating SLA compliance."
            )

        if status == "PASS":
            return (
                "Network service is meeting the configured SLA targets."
            )

        if not breached_metrics:
            return (
                "SLA compliance is below target. "
                "Review recent network metrics."
            )

        metrics = ", ".join(
            breached_metrics
        )

        if status == "WARNING":
            return (
                "SLA compliance is approaching the breach threshold. "
                f"Review: {metrics}."
            )

        return (
            "SLA breach detected. "
            f"Investigate: {metrics}."
        )

    @staticmethod
    def calculate(
        statuses: list[str],
        latencies_ms: list[float],
        packet_losses_percent: list[float],
        jitters_ms: list[float],
        thresholds: SLAThresholds | None = None,
    ) -> SLAResult:
        thresholds = thresholds or SLAThresholds()

        samples_analyzed = max(
            len(statuses),
            len(latencies_ms),
            len(packet_losses_percent),
            len(jitters_ms),
        )

        availability = SLAService.calculate_availability(
            statuses=statuses,
        )

        latency_compliance = SLAService.calculate_compliance(
            values=latencies_ms,
            maximum_allowed=thresholds.latency_ms,
        )

        packet_loss_compliance = (
            SLAService.calculate_compliance(
                values=packet_losses_percent,
                maximum_allowed=(
                    thresholds.packet_loss_percent
                ),
            )
        )

        jitter_compliance = SLAService.calculate_compliance(
            values=jitters_ms,
            maximum_allowed=thresholds.jitter_ms,
        )

        if samples_analyzed == 0:
            overall_compliance = 0
        else:
            overall_compliance = round(
                availability * 0.40
                + latency_compliance * 0.20
                + packet_loss_compliance * 0.25
                + jitter_compliance * 0.15,
                2,
            )

        status = SLAService.classify_status(
            compliance=overall_compliance,
            samples_analyzed=samples_analyzed,
            thresholds=thresholds,
        )

        breached_metrics = []

        if (
            availability
            < thresholds.pass_compliance_percent
        ):
            breached_metrics.append("availability")

        if (
            latency_compliance
            < thresholds.pass_compliance_percent
        ):
            breached_metrics.append("latency")

        if (
            packet_loss_compliance
            < thresholds.pass_compliance_percent
        ):
            breached_metrics.append("packet_loss")

        if (
            jitter_compliance
            < thresholds.pass_compliance_percent
        ):
            breached_metrics.append("jitter")

        return SLAResult(
            samples_analyzed=samples_analyzed,
            availability_percent=availability,
            latency_compliance_percent=latency_compliance,
            packet_loss_compliance_percent=(
                packet_loss_compliance
            ),
            jitter_compliance_percent=jitter_compliance,
            overall_compliance_percent=overall_compliance,
            status=status,
            breached_metrics=breached_metrics,
            recommendation=SLAService.build_recommendation(
                status=status,
                breached_metrics=breached_metrics,
            ),
        )