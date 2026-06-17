from pydantic import BaseModel


class NetworkImpactResponse(BaseModel):
    impact_score: int
    status: str
    affected_services: list[str]
    message: str

    average_latency_ms: float
    average_packet_loss_percent: float
    average_jitter_ms: float