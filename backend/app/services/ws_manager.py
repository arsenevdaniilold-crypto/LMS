import asyncio
import uuid
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.setdefault(user_id, []).append(ws)

    async def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return
            try:
                sockets.remove(ws)
            except ValueError:
                pass
            if not sockets:
                self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: uuid.UUID, message: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(user_id, []))
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(user_id, ws)


ws_manager = ConnectionManager()
