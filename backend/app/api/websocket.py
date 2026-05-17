from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dashboard_cache import get_dashboard_state
from app.core.device_state_cache import get_all_device_states


router = APIRouter(tags=["WebSocket"])


class WebSocketConnectionManager:

    def __init__(self, name: str):
        self.name = name
        self.active_connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.active_connections.append(websocket)

        print(
            f"{self.name} websocket connected. "
            f"Active connections: {len(self.active_connections)}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print(
            f"{self.name} websocket disconnected. "
            f"Active connections: {len(self.active_connections)}"
        )

    async def broadcast(
        self,
        message: dict,
    ):
        disconnected_connections: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(connection)


dashboard_manager = WebSocketConnectionManager(name="Dashboard")
device_state_manager = WebSocketConnectionManager(name="Device state")


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await dashboard_manager.connect(websocket)

    cached_state = get_dashboard_state()

    if cached_state:
        await websocket.send_json(cached_state)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)


@router.websocket("/ws/devices/live")
async def device_state_websocket(websocket: WebSocket):
    await device_state_manager.connect(websocket)

    cached_device_states = get_all_device_states()

    if cached_device_states:
        await websocket.send_json(cached_device_states)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        device_state_manager.disconnect(websocket)