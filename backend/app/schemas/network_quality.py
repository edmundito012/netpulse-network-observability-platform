from pydantic import BaseModel


class NetworkQualityResponse(BaseModel):
    average_latency: float
    median_latency: float

    minimum_latency: float
    maximum_latency: float

    p95_latency: float
    p99_latency: float

    latency_std_deviation: float

    stability_score: int

    quality_grade: str