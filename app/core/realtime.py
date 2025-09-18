from typing import Dict, Set, Any
from fastapi import WebSocket
from asyncio import Lock
import json

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._lock = Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        message = json.dumps({
            "type": event_type,
            "ts": payload.get("ts"),
            "data": payload.get("data", payload),
            "source": "server",
            "version": 1,
        }, ensure_ascii=False)
        dead: Set[WebSocket] = set()
        async with self._lock:
            for ws in self.active_connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                try:
                    self.active_connections.remove(ws)
                except KeyError:
                    pass

manager = ConnectionManager()
