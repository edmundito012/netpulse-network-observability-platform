from pydantic import BaseModel


class NetworkHealthScoreResponse(BaseModel):
    health_score: int

    grade: str

    latency_score: int
    jitter_score: int
    packet_loss_score: int
    stability_score: int

    bottleneck: str

    recommendation: str