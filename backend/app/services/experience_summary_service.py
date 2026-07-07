from dataclasses import dataclass


@dataclass
class ExperienceProfileResult:
    score: int
    status: str


@dataclass
class ExperienceSummaryResult:
    overall_qoe_score: int
    overall_status: str

    gaming: ExperienceProfileResult
    streaming: ExperienceProfileResult

    recommendation: str


class ExperienceSummaryService:

    @staticmethod
    def classify(score: int) -> str:

        if score >= 95:
            return "EXCELLENT"

        if score >= 80:
            return "GOOD"

        if score >= 65:
            return "FAIR"

        return "POOR"

    @staticmethod
    def recommendation(score: int):

        if score >= 90:
            return (
                "Network ready for gaming, streaming and remote work."
            )

        if score >= 75:
            return (
                "Minor degradation detected."
            )

        if score >= 60:
            return (
                "Network quality is unstable."
            )

        return (
            "Poor user experience expected."
        )

    @staticmethod
    def build(
        gaming_score: int,
        streaming_score: int,
    ):

        overall = round(
            (
                gaming_score +
                streaming_score
            ) / 2
        )

        return ExperienceSummaryResult(

            overall_qoe_score=overall,

            overall_status=(
                ExperienceSummaryService
                .classify(overall)
            ),

            gaming=ExperienceProfileResult(
                score=gaming_score,
                status=(
                    ExperienceSummaryService
                    .classify(gaming_score)
                ),
            ),

            streaming=ExperienceProfileResult(
                score=streaming_score,
                status=(
                    ExperienceSummaryService
                    .classify(streaming_score)
                ),
            ),

            recommendation=(
                ExperienceSummaryService
                .recommendation(
                    overall
                )
            ),
        )