from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["WebSocket"])


class DashboardConnectionManager:

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.active_connections.append(websocket)

        print(
            "Dashboard websocket connected. "
            f"Active connections: {len(self.active_connections)}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print(
            "Dashboard websocket disconnected. "
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


dashboard_manager = DashboardConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await dashboard_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)