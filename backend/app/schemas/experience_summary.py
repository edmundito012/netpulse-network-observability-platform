from pydantic import BaseModel


class ExperienceProfile(BaseModel):
    score: int
    status: str


class ExperienceSummaryResponse(BaseModel):
    overall_qoe_score: int
    overall_status: str

    gaming: ExperienceProfile
    streaming: ExperienceProfile

    recommendation: str