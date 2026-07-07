from dataclasses import dataclass
from statistics import mean
from statistics import pstdev


@dataclass
class NetworkAnomalyResult:
    metric_name: str

    latest_value: float
    baseline_average: float
    baseline_std_deviation: float

    z_score: float

    severity: str
    confidence: str

    anomaly_detected: bool

    recommendation: str


class NetworkAnomalyService:

    @staticmethod
    def calculate_z_score(
        latest_value: float,
        average: float,
        std_deviation: float,
    ) -> float:
        if std_deviation == 0:
            return 0

        return round(
            (latest_value - average) / std_deviation,
            2,
        )

    @staticmethod
    def classify_severity(
        z_score: float,
    ) -> str:
        absolute_z_score = abs(z_score)

        if absolute_z_score >= 3:
            return "CRITICAL"

        if absolute_z_score >= 2:
            return "WARNING"

        return "NORMAL"

    @staticmethod
    def classify_confidence(
        z_score: float,
        sample_count: int,
    ) -> str:
        absolute_z_score = abs(z_score)

        if sample_count < 5:
            return "LOW"

        if absolute_z_score >= 3:
            return "VERY_HIGH"

        if absolute_z_score >= 2:
            return "HIGH"

        return "MEDIUM"

    @staticmethod
    def build_recommendation(
        metric_name: str,
        severity: str,
    ) -> str:
        if severity == "CRITICAL":
            return (
                f"Critical anomaly detected for {metric_name}. "
                "Investigate recent network behavior immediately."
            )

        if severity == "WARNING":
            return (
                f"Unusual behavior detected for {metric_name}. "
                "Monitor this metric closely."
            )

        return (
            f"{metric_name} is within normal baseline range."
        )

    @staticmethod
    def analyze(
        values: list[float],
        metric_name: str,
    ) -> NetworkAnomalyResult:
        if not values:
            return NetworkAnomalyResult(
                metric_name=metric_name,
                latest_value=0,
                baseline_average=0,
                baseline_std_deviation=0,
                z_score=0,
                severity="UNKNOWN",
                confidence="LOW",
                anomaly_detected=False,
                recommendation=(
                    f"No samples available for {metric_name}."
                ),
            )

        if len(values) == 1:
            latest_value = values[-1]

            return NetworkAnomalyResult(
                metric_name=metric_name,
                latest_value=latest_value,
                baseline_average=latest_value,
                baseline_std_deviation=0,
                z_score=0,
                severity="NORMAL",
                confidence="LOW",
                anomaly_detected=False,
                recommendation=(
                    f"Not enough baseline samples for {metric_name}."
                ),
            )

        baseline_values = values[:-1]
        latest_value = values[-1]

        baseline_average = mean(baseline_values)
        baseline_std_deviation = pstdev(
            baseline_values,
        )

        z_score = (
            NetworkAnomalyService.calculate_z_score(
                latest_value=latest_value,
                average=baseline_average,
                std_deviation=baseline_std_deviation,
            )
        )

        severity = (
            NetworkAnomalyService.classify_severity(
                z_score,
            )
        )

        return NetworkAnomalyResult(
            metric_name=metric_name,
            latest_value=latest_value,
            baseline_average=round(
                baseline_average,
                2,
            ),
            baseline_std_deviation=round(
                baseline_std_deviation,
                2,
            ),
            z_score=z_score,
            severity=severity,
            confidence=(
                NetworkAnomalyService
                .classify_confidence(
                    z_score=z_score,
                    sample_count=len(values),
                )
            ),
            anomaly_detected=severity in [
                "WARNING",
                "CRITICAL",
            ],
            recommendation=(
                NetworkAnomalyService
                .build_recommendation(
                    metric_name=metric_name,
                    severity=severity,
                )
            ),
        )