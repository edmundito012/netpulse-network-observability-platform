from pydantic import BaseModel


class HealthScoreRead(BaseModel):
    device_id: int
    device_name: str
    score: int
    status: str