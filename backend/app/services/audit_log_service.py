from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:

    @staticmethod
    def log(
        db: Session,
        user_id: int | None,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        details: dict | None = None,
    ):
        return AuditLogRepository.create(
            db=db,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )