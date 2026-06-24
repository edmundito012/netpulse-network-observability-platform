from app.services.providers.base_notification_provider import (
    BaseNotificationProvider,
)


class TelegramProvider(
    BaseNotificationProvider
):

    def send(
        self,
        title: str,
        body: str,
    ) -> bool:

        message = (
            f"🚨 {title}\n\n"
            f"{body}"
        )

        print(message)

        return True