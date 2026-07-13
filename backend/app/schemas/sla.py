from pydantic import BaseModel


class SLAResponse(BaseModel):
    samples_analyzed: int

    availability_percent: float
    latency_compliance_percent: float
    packet_loss_compliance_percent: float
    jitter_compliance_percent: float

    overall_compliance_percent: float

    status: str
    breached_metrics: list[str]
    recommendation: str