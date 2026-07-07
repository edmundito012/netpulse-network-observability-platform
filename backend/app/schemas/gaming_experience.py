from pydantic import BaseModel


class GamingExperienceResponse(BaseModel):
    gaming_score: int
    competitive_ready: bool

    ping_stability: str
    lag_spike_risk: str
    rubber_banding_risk: str
    hit_registration: str

    recommended_games: list[str]
    recommendation: str