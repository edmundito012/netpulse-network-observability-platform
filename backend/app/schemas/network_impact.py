from pydantic import BaseModel


class NetworkImpactResponse(BaseModel):
    impact_score: int
    status: str
    affected_services: list[str]
    message: str