from app.models.notification_log import (
    NotificationLog,
)


def test_notification_log_model():

    log = NotificationLog(
        provider="telegram",
        title="Predictive Alert",
        status="SENT",
    )

    assert log.provider == "telegram"

    assert log.status == "SENT"