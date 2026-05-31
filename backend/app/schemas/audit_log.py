from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource_type: str
    resource_id: int | None
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)