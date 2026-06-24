from sqlalchemy.orm import Session

from app.models.notification_log import (
    NotificationLog,
)


class NotificationLogService:

    @staticmethod
    def create(
        db: Session,
        provider: str,
        title: str,
        status: str,
    ):

        log = NotificationLog(
            provider=provider,
            title=title,
            status=status,
        )

        db.add(log)
        db.commit()

        return log