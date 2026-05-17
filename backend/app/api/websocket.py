import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.dashboard_service import DashboardService


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()

    db: Session = SessionLocal()

    try:
        while True:
            overview = DashboardService.get_overview(db=db)

            await websocket.send_json(
                jsonable_encoder(overview)
            )

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        print("Dashboard websocket disconnected")

    finally:
        db.close()