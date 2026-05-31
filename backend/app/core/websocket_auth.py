from jose import JWTError, jwt

from fastapi import WebSocket

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def authenticate_websocket(
    websocket: WebSocket,
    db: Session,
) -> User | None:
    token = websocket.query_params.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        email = payload.get("sub")

        if email is None:
            return None

    except JWTError:
        return None

    return UserRepository.get_by_email(
        db,
        email,
    )