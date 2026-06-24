from app.services.notification_service import (
    NotificationService,
)

from app.services.providers.telegram_provider import (
    TelegramProvider,
)


class PredictiveNotificationService:

    @staticmethod
    def send_predictive_alert(
        device_name: str,
        risk_score: int,
        reason: str,
    ) -> bool:

        notification = (
            NotificationService
            .build_predictive_alert_message(
                device_name=device_name,
                risk_score=risk_score,
                reason=reason,
            )
        )

        provider = TelegramProvider()

        return provider.send(
            title=notification.title,
            body=notification.body,
        )