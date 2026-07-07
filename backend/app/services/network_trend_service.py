from dataclasses import dataclass
from statistics import mean
from statistics import median
from statistics import pstdev


@dataclass
class NetworkTrendResult:
    trend: str

    average: float
    median: float
    minimum: float
    maximum: float

    slope: float
    growth_percent: float
    moving_average: float

    volatility: str

    predicted_next_latency: float

    confidence: str
    risk: str

    recommendation: str


class NetworkTrendService:

    STABLE_SLOPE_THRESHOLD = 0.5

    @staticmethod
    def calculate_slope(
        values: list[float],
    ) -> float:
        if len(values) < 2:
            return 0

        n = len(values)

        x_values = list(range(n))

        x_mean = mean(x_values)
        y_mean = mean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(
                x_values,
                values,
            )
        )

        denominator = sum(
            (x - x_mean) ** 2
            for x in x_values
        )

        if denominator == 0:
            return 0

        return round(
            numerator / denominator,
            2,
        )

    @staticmethod
    def classify_trend(
        slope: float,
    ) -> str:
        if slope > NetworkTrendService.STABLE_SLOPE_THRESHOLD:
            return "INCREASING"

        if slope < -NetworkTrendService.STABLE_SLOPE_THRESHOLD:
            return "DECREASING"

        return "STABLE"

    @staticmethod
    def calculate_growth_percent(
        values: list[float],
    ) -> float:
        if len(values) < 2:
            return 0

        first = values[0]
        last = values[-1]

        if first == 0:
            return 0

        return round(
            ((last - first) / first) * 100,
            2,
        )

    @staticmethod
    def calculate_moving_average(
        values: list[float],
        window: int = 5,
    ) -> float:
        if not values:
            return 0

        if len(values) < window:
            window_values = values
        else:
            window_values = values[-window:]

        return round(
            mean(window_values),
            2,
        )

    @staticmethod
    def classify_volatility(
        std_deviation: float,
    ) -> str:
        if std_deviation > 6:
            return "HIGH"

        if std_deviation >= 2:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_confidence(
        volatility: str,
        sample_count: int,
    ) -> str:
        if sample_count < 5:
            return "LOW"

        if volatility == "LOW":
            return "HIGH"

        if volatility == "MEDIUM":
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def classify_risk(
        trend: str,
        volatility: str,
        predicted_next_latency: float,
    ) -> str:
        if (
            predicted_next_latency >= 120
            or volatility == "HIGH"
        ):
            return "HIGH"

        if (
            predicted_next_latency >= 70
            or trend == "INCREASING"
        ):
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def build_recommendation(
        trend: str,
        risk: str,
    ) -> str:
        if risk == "HIGH":
            return (
                "High network degradation risk detected. "
                "Investigate WAN utilization, packet loss, and jitter."
            )

        if trend == "INCREASING":
            return (
                "Latency is increasing. Monitor WAN utilization."
            )

        if trend == "DECREASING":
            return (
                "Latency trend is improving."
            )

        return (
            "Network latency trend is stable."
        )

    @staticmethod
    def analyze(
        values: list[float],
    ) -> NetworkTrendResult:
        if not values:
            return NetworkTrendResult(
                trend="UNKNOWN",
                average=0,
                median=0,
                minimum=0,
                maximum=0,
                slope=0,
                growth_percent=0,
                moving_average=0,
                volatility="UNKNOWN",
                predicted_next_latency=0,
                confidence="LOW",
                risk="UNKNOWN",
                recommendation="No latency samples available.",
            )

        slope = NetworkTrendService.calculate_slope(values)

        trend = NetworkTrendService.classify_trend(
            slope,
        )

        std_deviation = pstdev(values)

        volatility = NetworkTrendService.classify_volatility(
            std_deviation,
        )

        predicted_next_latency = round(
            values[-1] + slope,
            2,
        )

        risk = NetworkTrendService.classify_risk(
            trend=trend,
            volatility=volatility,
            predicted_next_latency=predicted_next_latency,
        )

        return NetworkTrendResult(
            trend=trend,
            average=round(
                mean(values),
                2,
            ),
            median=round(
                median(values),
                2,
            ),
            minimum=min(values),
            maximum=max(values),
            slope=slope,
            growth_percent=(
                NetworkTrendService
                .calculate_growth_percent(values)
            ),
            moving_average=(
                NetworkTrendService
                .calculate_moving_average(values)
            ),
            volatility=volatility,
            predicted_next_latency=predicted_next_latency,
            confidence=(
                NetworkTrendService
                .classify_confidence(
                    volatility=volatility,
                    sample_count=len(values),
                )
            ),
            risk=risk,
            recommendation=(
                NetworkTrendService
                .build_recommendation(
                    trend=trend,
                    risk=risk,
                )
            ),
        )