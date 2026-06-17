from pydantic import BaseModel


class GamingImpactResponse(BaseModel):
    impact_score: int
    status: str

    gaming_quality: str

    lag_risk: str
    packet_loss_risk: str
    jitter_risk: str

    recommended_action: str