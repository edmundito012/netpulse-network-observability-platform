import asyncio
from datetime import UTC
from unittest.mock import AsyncMock, Mock

from app.api.websocket import WebSocketConnectionManager


def test_connect_accepts_and_tracks_websocket(monkeypatch):
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    websocket.accept = AsyncMock()
    update_metric = Mock()
    monkeypatch.setattr(manager, "update_connection_metric", update_metric)

    asyncio.run(manager.connect(websocket))

    websocket.accept.assert_awaited_once_with()
    assert manager.active_connections == [websocket]
    assert manager.connection_last_seen[websocket].tzinfo is UTC
    update_metric.assert_called_once_with()


def test_disconnect_removes_tracked_websocket(monkeypatch):
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    manager.active_connections = [websocket]
    manager.connection_last_seen = {websocket: Mock()}
    update_metric = Mock()
    monkeypatch.setattr(manager, "update_connection_metric", update_metric)

    manager.disconnect(websocket)

    assert manager.active_connections == []
    assert manager.connection_last_seen == {}
    update_metric.assert_called_once_with()


def test_send_initial_state_skips_empty_state():
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    websocket.send_json = AsyncMock()
    manager.disconnect = Mock()

    asyncio.run(
        manager.send_initial_state(
            websocket=websocket,
            state={},
        )
    )

    websocket.send_json.assert_not_awaited()
    manager.disconnect.assert_not_called()


def test_send_initial_state_sends_state():
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    websocket.send_json = AsyncMock()
    state = {"status": "healthy"}

    asyncio.run(
        manager.send_initial_state(
            websocket=websocket,
            state=state,
        )
    )

    websocket.send_json.assert_awaited_once_with(state)


def test_send_initial_state_disconnects_after_error():
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    websocket.send_json = AsyncMock(side_effect=RuntimeError("send failed"))
    manager.disconnect = Mock()

    asyncio.run(
        manager.send_initial_state(
            websocket=websocket,
            state={"status": "healthy"},
        )
    )

    manager.disconnect.assert_called_once_with(websocket)


def test_broadcast_disconnects_only_failed_connections(monkeypatch):
    manager = WebSocketConnectionManager(name="Test")
    healthy = Mock()
    healthy.send_json = AsyncMock()
    failed = Mock()
    failed.send_json = AsyncMock(side_effect=RuntimeError("send failed"))

    manager.active_connections = [healthy, failed]
    manager.connection_last_seen = {
        healthy: Mock(),
        failed: Mock(),
    }
    monkeypatch.setattr(manager, "update_connection_metric", Mock())

    message = {"type": "update"}
    asyncio.run(manager.broadcast(message))

    healthy.send_json.assert_awaited_once_with(message)
    failed.send_json.assert_awaited_once_with(message)
    assert manager.active_connections == [healthy]
    assert healthy in manager.connection_last_seen
    assert failed not in manager.connection_last_seen


def test_heartbeat_sends_ping_and_disconnects_after_error(monkeypatch):
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()
    websocket.send_json = AsyncMock()
    manager.disconnect = Mock()
    sleep_calls = 0

    async def fake_sleep(_seconds):
        nonlocal sleep_calls
        sleep_calls += 1

        if sleep_calls > 1:
            raise RuntimeError("connection closed")

    monkeypatch.setattr(
        "app.api.websocket.asyncio.sleep",
        fake_sleep,
    )

    asyncio.run(manager.heartbeat_loop(websocket))

    websocket.send_json.assert_awaited_once()
    message = websocket.send_json.await_args.args[0]
    assert message["type"] == "ping"
    assert isinstance(message["timestamp"], str)
    manager.disconnect.assert_called_once_with(websocket)


def test_update_last_seen_tracks_websocket():
    manager = WebSocketConnectionManager(name="Test")
    websocket = Mock()

    manager.update_last_seen(websocket)

    assert manager.connection_last_seen[websocket].tzinfo is UTC
