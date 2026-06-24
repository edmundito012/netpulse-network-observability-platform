import requests

from app.core.config import settings
from app.services.providers.base_notification_provider import (
    BaseNotificationProvider,
)


class TelegramProvider(BaseNotificationProvider):

    def send(
        self,
        title: str,
        body: str,
    ) -> bool:
        if (
            not settings.TELEGRAM_BOT_TOKEN
            or not settings.TELEGRAM_CHAT_ID
        ):
            return False

        message = (
            f"🚨 {title}\n\n"
            f"{body}"
        )

        url = (
            f"https://api.telegram.org/bot"
            f"{settings.TELEGRAM_BOT_TOKEN}"
            f"/sendMessage"
        )

        response = requests.post(
            url,
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
            },
            timeout=10,
        )

        return response.status_code == 200