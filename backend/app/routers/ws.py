import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session_maker
from app.models.user import User
from app.services.ws_manager import ws_manager
from app.utils.security import decode_access_token

router = APIRouter()


async def _authenticate(access_token: str | None) -> User | None:
    if not access_token:
        return None
    payload = decode_access_token(access_token)
    if payload is None:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    access_token = websocket.cookies.get("access_token")
    user = await _authenticate(access_token)
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await ws_manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(user.id, websocket)
