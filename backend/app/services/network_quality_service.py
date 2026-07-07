from dataclasses import dataclass
from math import floor
from statistics import mean
from statistics import median
from statistics import pstdev


@dataclass
class NetworkQualityResult:
    average_latency: float
    median_latency: float

    minimum_latency: float
    maximum_latency: float

    p95_latency: float
    p99_latency: float

    latency_std_deviation: float

    stability_score: int

    quality_grade: str


class NetworkQualityService:

    @staticmethod
    def percentile(
        values: list[float],
        percentile: float,
    ) -> float:
        if not values:
            return 0

        if percentile <= 0:
            return min(values)

        if percentile >= 1:
            return max(values)

        sorted_values = sorted(values)

        position = (
            (len(sorted_values) - 1)
            * percentile
        )

        lower_index = floor(position)
        upper_index = min(
            lower_index + 1,
            len(sorted_values) - 1,
        )

        lower_value = sorted_values[lower_index]
        upper_value = sorted_values[upper_index]

        weight = position - lower_index

        interpolated_value = (
            lower_value
            + (upper_value - lower_value) * weight
        )

        return round(interpolated_value, 2)

    @staticmethod
    def stability_score(
        std: float,
    ) -> int:
        score = 100 - (std * 4)

        score = max(
            0,
            min(score, 100),
        )

        return int(score)

    @staticmethod
    def grade(
        score: int,
    ) -> str:
        if score >= 97:
            return "A+"

        if score >= 90:
            return "A"

        if score >= 80:
            return "B"

        if score >= 70:
            return "C"

        if score >= 60:
            return "D"

        return "F"

    @staticmethod
    def analyze(
        latencies: list[float],
    ) -> NetworkQualityResult:
        if not latencies:
            return NetworkQualityResult(
                average_latency=0,
                median_latency=0,
                minimum_latency=0,
                maximum_latency=0,
                p95_latency=0,
                p99_latency=0,
                latency_std_deviation=0,
                stability_score=100,
                quality_grade="A+",
            )

        std = pstdev(latencies)

        stability = (
            NetworkQualityService
            .stability_score(std)
        )

        return NetworkQualityResult(
            average_latency=round(
                mean(latencies),
                2,
            ),
            median_latency=round(
                median(latencies),
                2,
            ),
            minimum_latency=min(latencies),
            maximum_latency=max(latencies),
            p95_latency=(
                NetworkQualityService
                .percentile(
                    latencies,
                    0.95,
                )
            ),
            p99_latency=(
                NetworkQualityService
                .percentile(
                    latencies,
                    0.99,
                )
            ),
            latency_std_deviation=round(
                std,
                2,
            ),
            stability_score=stability,
            quality_grade=(
                NetworkQualityService
                .grade(stability)
            ),
        )