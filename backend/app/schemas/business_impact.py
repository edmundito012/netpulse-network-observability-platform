from pydantic import BaseModel


class BusinessImpactResponse(BaseModel):
    impact_score: int
    status: str

    teams_quality: str
    zoom_quality: str
    voip_quality: str
    vpn_quality: str