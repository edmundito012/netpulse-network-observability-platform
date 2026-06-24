from dataclasses import dataclass


@dataclass
class LatencyIntelligenceResult:
    average_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float

    latency_spread_ms: float

    latency_spike_detected: bool

    latency_stability: str


class LatencyIntelligenceService:

    SPIKE_THRESHOLD_MS = 100

    @staticmethod
    def analyze(
        latencies: list[float],
    ) -> LatencyIntelligenceResult:

        if not latencies:

            return LatencyIntelligenceResult(
                average_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                latency_spread_ms=0,
                latency_spike_detected=False,
                latency_stability="UNKNOWN",
            )

        average_latency = (
            sum(latencies)
            / len(latencies)
        )

        min_latency = min(latencies)

        max_latency = max(latencies)

        spread = (
            max_latency
            - min_latency
        )

        spike_detected = (
            max_latency
            - average_latency
            >= LatencyIntelligenceService.SPIKE_THRESHOLD_MS
        )

        if spread >= 80:

            stability = "UNSTABLE"

        elif spread >= 40:

            stability = "DEGRADED"

        else:

            stability = "STABLE"

        return LatencyIntelligenceResult(
            average_latency_ms=round(
                average_latency,
                2,
            ),
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            latency_spread_ms=round(
                spread,
                2,
            ),
            latency_spike_detected=spike_detected,
            latency_stability=stability,
        )