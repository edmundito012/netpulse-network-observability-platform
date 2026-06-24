from app.services.providers.telegram_provider import TelegramProvider


def test_provider_creation():
    provider = TelegramProvider()

    assert provider is not None


def test_send_returns_false_without_credentials(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(
        settings,
        "TELEGRAM_BOT_TOKEN",
        None,
    )

    monkeypatch.setattr(
        settings,
        "TELEGRAM_CHAT_ID",
        None,
    )

    provider = TelegramProvider()

    result = provider.send(
        title="Test Alert",
        body="Latency spike detected",
    )

    assert result is False