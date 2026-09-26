import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import WebSocketDisconnect

from app.api import websocket as websocket_api
from app.api.websocket import WebSocketConnectionManager


def create_manager():
    return SimpleNamespace(
        connect=AsyncMock(),
        disconnect=Mock(),
        send_initial_state=AsyncMock(),
        heartbeat_loop=AsyncMock(),
        update_last_seen=Mock(),
    )


def test_connection_metric_uses_active_connection_count(monkeypatch):
    manager = WebSocketConnectionManager(name="Test")
    manager.active_connections = [Mock(), Mock()]
    gauge = Mock()
    labels = Mock(return_value=gauge)

    monkeypatch.setattr(
        websocket_api.active_websocket_connections,
        "labels",
        labels,
    )

    manager.update_connection_metric()

    labels.assert_called_once_with(channel="Test")
    gauge.set.assert_called_once_with(2)


def test_dashboard_websocket_rejects_unauthenticated_user(monkeypatch):
    websocket = Mock()
    websocket.close = AsyncMock()
    manager = create_manager()

    monkeypatch.setattr(
        websocket_api,
        "authenticate_websocket",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(websocket_api, "dashboard_manager", manager)

    asyncio.run(
        websocket_api.dashboard_websocket(
            websocket=websocket,
            db=object(),
        )
    )

    websocket.close.assert_awaited_once_with(
        code=1008,
        reason="Authentication required",
    )
    manager.connect.assert_not_awaited()


def test_dashboard_websocket_handles_authenticated_session(monkeypatch):
    websocket = Mock()
    websocket.receive_text = AsyncMock(side_effect=["message", WebSocketDisconnect()])
    manager = create_manager()
    state = {"status": "healthy"}

    monkeypatch.setattr(
        websocket_api,
        "authenticate_websocket",
        AsyncMock(return_value=SimpleNamespace(email="user@example.com")),
    )
    monkeypatch.setattr(websocket_api, "dashboard_manager", manager)
    monkeypatch.setattr(
        websocket_api,
        "get_dashboard_state",
        Mock(return_value=state),
    )

    asyncio.run(
        websocket_api.dashboard_websocket(
            websocket=websocket,
            db=object(),
        )
    )

    manager.connect.assert_awaited_once_with(websocket)
    manager.send_initial_state.assert_awaited_once_with(
        websocket=websocket,
        state=state,
    )
    manager.update_last_seen.assert_called_once_with(websocket)
    manager.disconnect.assert_called_once_with(websocket)


def test_device_state_websocket_rejects_unauthenticated_user(monkeypatch):
    websocket = Mock()
    websocket.close = AsyncMock()
    manager = create_manager()

    monkeypatch.setattr(
        websocket_api,
        "authenticate_websocket",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(websocket_api, "device_state_manager", manager)

    asyncio.run(
        websocket_api.device_state_websocket(
            websocket=websocket,
            db=object(),
        )
    )

    websocket.close.assert_awaited_once_with(
        code=1008,
        reason="Authentication required",
    )
    manager.connect.assert_not_awaited()


def test_device_state_websocket_handles_authenticated_session(monkeypatch):
    websocket = Mock()
    websocket.receive_text = AsyncMock(side_effect=["message", WebSocketDisconnect()])
    manager = create_manager()
    state = {"device-1": {"status": "up"}}

    monkeypatch.setattr(
        websocket_api,
        "authenticate_websocket",
        AsyncMock(return_value=SimpleNamespace(email="user@example.com")),
    )
    monkeypatch.setattr(websocket_api, "device_state_manager", manager)
    monkeypatch.setattr(
        websocket_api,
        "get_all_device_states",
        Mock(return_value=state),
    )

    asyncio.run(
        websocket_api.device_state_websocket(
            websocket=websocket,
            db=object(),
        )
    )

    manager.connect.assert_awaited_once_with(websocket)
    manager.send_initial_state.assert_awaited_once_with(
        websocket=websocket,
        state=state,
    )
    manager.update_last_seen.assert_called_once_with(websocket)
    manager.disconnect.assert_called_once_with(websocket)
