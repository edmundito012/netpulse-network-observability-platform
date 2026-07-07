from pydantic import BaseModel


class NetworkTrendResponse(BaseModel):
    trend: str

    average: float
    median: float
    minimum: float
    maximum: float

    slope: float
    growth_percent: float
    moving_average: float

    volatility: str

    predicted_next_latency: float

    confidence: str
    risk: str

    recommendation: str