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

    @staticmethod
    def get_history(
        db: Session,
    ):
        return (
            db.query(NotificationLog)
            .order_by(
                NotificationLog.sent_at.desc()
            )
            .limit(100)
            .all()
        )