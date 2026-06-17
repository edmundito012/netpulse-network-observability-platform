from pydantic import BaseModel


class DeviceRiskRead(BaseModel):
    device_id: int
    device_name: str

    risk_score: int
    risk_level: str