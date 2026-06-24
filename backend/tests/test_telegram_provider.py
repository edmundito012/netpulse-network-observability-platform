from app.services.providers.telegram_provider import (
    TelegramProvider,
)


def test_send_notification():

    provider = TelegramProvider()

    result = provider.send(
        title="Test Alert",
        body="Latency spike detected",
    )

    assert result is True