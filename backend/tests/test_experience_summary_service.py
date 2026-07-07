from app.services.experience_summary_service import (
    ExperienceSummaryService,
)


def test_summary():

    result = (
        ExperienceSummaryService.build(
            gaming_score=95,
            streaming_score=90,
        )
    )

    assert result.overall_qoe_score >= 90
    assert result.overall_status == "GOOD"


def test_excellent_summary():

    result = (
        ExperienceSummaryService.build(
            gaming_score=98,
            streaming_score=96,
        )
    )

    assert result.overall_status == "EXCELLENT"