import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dashboard_cache import get_dashboard_state
from app.core.device_state_cache import get_all_device_states
from app.core.logging import logger


router = APIRouter(tags=["WebSocket"])


class WebSocketConnectionManager:

    def __init__(self, name: str):
        self.name = name
        self.active_connections: list[WebSocket] = []
        self.connection_last_seen: dict[WebSocket, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_connections.append(websocket)

        self.connection_last_seen[websocket] = datetime.now(UTC)

        logger.info(
            "%s websocket connected. Active connections: %s",
            self.name,
            len(self.active_connections),
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_last_seen:
            del self.connection_last_seen[websocket]

        logger.info(
            "%s websocket disconnected. Active connections: %s",
            self.name,
            len(self.active_connections),
        )

    async def send_initial_state(
        self,
        websocket: WebSocket,
        state: dict,
    ):
        if not state:
            logger.info(
                "%s websocket connected with empty initial state",
                self.name,
            )
            return

        try:
            await websocket.send_json(state)

            logger.info(
                "%s initial state sent",
                self.name,
            )

        except Exception as e:
            logger.error(
                "%s initial state send error: %s",
                self.name,
                e,
            )

            self.disconnect(websocket)

    async def broadcast(
        self,
        message: dict,
    ):
        disconnected_connections: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)

            except Exception as e:
                logger.warning(
                    "%s websocket broadcast failed: %s",
                    self.name,
                    e,
                )

                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(connection)

        if self.active_connections:
            logger.info(
                "%s broadcast sent to %s active connections",
                self.name,
                len(self.active_connections),
            )

    async def heartbeat_loop(
        self,
        websocket: WebSocket,
    ):
        try:
            while True:
                await asyncio.sleep(30)

                await websocket.send_json(
                    {
                        "type": "ping",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

        except Exception:
            self.disconnect(websocket)

    def update_last_seen(
        self,
        websocket: WebSocket,
    ):
        self.connection_last_seen[websocket] = datetime.now(UTC)


dashboard_manager = WebSocketConnectionManager(name="Dashboard")
device_state_manager = WebSocketConnectionManager(name="Device state")


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await dashboard_manager.connect(websocket)

    await dashboard_manager.send_initial_state(
        websocket=websocket,
        state=get_dashboard_state(),
    )

    heartbeat_task = asyncio.create_task(
        dashboard_manager.heartbeat_loop(websocket)
    )

    try:
        while True:
            await websocket.receive_text()

            dashboard_manager.update_last_seen(websocket)

    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)

    finally:
        heartbeat_task.cancel()


@router.websocket("/ws/devices/live")
async def device_state_websocket(websocket: WebSocket):
    await device_state_manager.connect(websocket)

    await device_state_manager.send_initial_state(
        websocket=websocket,
        state=get_all_device_states(),
    )

    heartbeat_task = asyncio.create_task(
        device_state_manager.heartbeat_loop(websocket)
    )

    try:
        while True:
            await websocket.receive_text()

            device_state_manager.update_last_seen(websocket)

    except WebSocketDisconnect:
        device_state_manager.disconnect(websocket)

    finally:
        heartbeat_task.cancel()