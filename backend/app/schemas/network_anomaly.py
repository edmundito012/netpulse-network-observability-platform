from pydantic import BaseModel


class NetworkAnomalyResponse(BaseModel):
    metric_name: str

    latest_value: float
    baseline_average: float
    baseline_std_deviation: float

    z_score: float

    severity: str
    confidence: str

    anomaly_detected: bool

    recommendation: str