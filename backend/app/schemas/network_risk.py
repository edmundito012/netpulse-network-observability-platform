from pydantic import BaseModel


class NetworkRiskResponse(BaseModel):
    risk_score: int
    risk_level: str
    failure_probability: int
    contributing_factors: list[str]