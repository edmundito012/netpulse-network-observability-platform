from dataclasses import dataclass


@dataclass
class JitterIntelligenceResult:
    average_jitter_ms: float
    min_jitter_ms: float
    max_jitter_ms: float

    jitter_spread_ms: float

    jitter_spike_detected: bool
    degradation_detected: bool

    jitter_stability: str

    voip_risk: str
    gaming_risk: str


class JitterIntelligenceService:

    SPIKE_THRESHOLD_MS = 30

    @staticmethod
    def analyze(
        jitters: list[float],
    ) -> JitterIntelligenceResult:

        if not jitters:

            return JitterIntelligenceResult(
                average_jitter_ms=0,
                min_jitter_ms=0,
                max_jitter_ms=0,
                jitter_spread_ms=0,
                jitter_spike_detected=False,
                degradation_detected=False,
                jitter_stability="UNKNOWN",
                voip_risk="UNKNOWN",
                gaming_risk="UNKNOWN",
            )

        avg_jitter = (
            sum(jitters)
            / len(jitters)
        )

        min_jitter = min(jitters)
        max_jitter = max(jitters)

        spread = (
            max_jitter
            - min_jitter
        )

        spike_detected = (
            max_jitter
            - avg_jitter
            >= JitterIntelligenceService.SPIKE_THRESHOLD_MS
        )

        degradation_detected = (
            jitters[-1]
            > jitters[0] * 2
            and len(jitters) >= 5
        )

        if spread >= 25:
            stability = "UNSTABLE"

        elif spread >= 10:
            stability = "DEGRADED"

        else:
            stability = "STABLE"

        latest_jitter = jitters[-1]

        if latest_jitter >= 40:
            voip_risk = "HIGH"
        elif latest_jitter >= 20:
            voip_risk = "MEDIUM"
        else:
            voip_risk = "LOW"

        if latest_jitter >= 30:
            gaming_risk = "HIGH"
        elif latest_jitter >= 15:
            gaming_risk = "MEDIUM"
        else:
            gaming_risk = "LOW"

        return JitterIntelligenceResult(
            average_jitter_ms=round(
                avg_jitter,
                2,
            ),
            min_jitter_ms=min_jitter,
            max_jitter_ms=max_jitter,
            jitter_spread_ms=round(
                spread,
                2,
            ),
            jitter_spike_detected=spike_detected,
            degradation_detected=degradation_detected,
            jitter_stability=stability,
            voip_risk=voip_risk,
            gaming_risk=gaming_risk,
        )