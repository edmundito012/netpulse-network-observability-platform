import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from jose import JWTError

from app.core import websocket_auth


def authenticate(*, token, db):
    websocket = SimpleNamespace(query_params={} if token is None else {"token": token})

    return asyncio.run(
        websocket_auth.authenticate_websocket(
            websocket=websocket,
            db=db,
        )
    )


def test_missing_token_returns_none(monkeypatch):
    decode = Mock()
    get_by_email = Mock()

    monkeypatch.setattr(websocket_auth.jwt, "decode", decode)
    monkeypatch.setattr(
        websocket_auth.UserRepository,
        "get_by_email",
        get_by_email,
    )

    result = authenticate(token=None, db=object())

    assert result is None
    decode.assert_not_called()
    get_by_email.assert_not_called()


def test_invalid_token_returns_none(monkeypatch):
    decode = Mock(side_effect=JWTError("invalid token"))
    get_by_email = Mock()

    monkeypatch.setattr(websocket_auth.jwt, "decode", decode)
    monkeypatch.setattr(
        websocket_auth.UserRepository,
        "get_by_email",
        get_by_email,
    )

    result = authenticate(token="invalid", db=object())

    assert result is None
    get_by_email.assert_not_called()


def test_token_without_subject_returns_none(monkeypatch):
    decode = Mock(return_value={})
    get_by_email = Mock()

    monkeypatch.setattr(websocket_auth.jwt, "decode", decode)
    monkeypatch.setattr(
        websocket_auth.UserRepository,
        "get_by_email",
        get_by_email,
    )

    result = authenticate(token="valid", db=object())

    assert result is None
    get_by_email.assert_not_called()


def test_valid_token_returns_matching_user(monkeypatch):
    db = object()
    user = object()
    decode = Mock(return_value={"sub": "user@example.com"})
    get_by_email = Mock(return_value=user)

    monkeypatch.setattr(websocket_auth.jwt, "decode", decode)
    monkeypatch.setattr(
        websocket_auth.UserRepository,
        "get_by_email",
        get_by_email,
    )

    result = authenticate(token="valid", db=db)

    assert result is user
    decode.assert_called_once_with(
        "valid",
        websocket_auth.settings.SECRET_KEY,
        algorithms=[websocket_auth.settings.ALGORITHM],
    )
    get_by_email.assert_called_once_with(db, "user@example.com")


def test_unknown_user_returns_none(monkeypatch):
    db = object()

    monkeypatch.setattr(
        websocket_auth.jwt,
        "decode",
        Mock(return_value={"sub": "missing@example.com"}),
    )
    get_by_email = Mock(return_value=None)
    monkeypatch.setattr(
        websocket_auth.UserRepository,
        "get_by_email",
        get_by_email,
    )

    result = authenticate(token="valid", db=db)

    assert result is None
    get_by_email.assert_called_once_with(db, "missing@example.com")
