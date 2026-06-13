from pydantic import BaseModel


class TopRiskDeviceRead(BaseModel):
    device_id: int
    device_name: str
    health_score: int
    failure_risk: int