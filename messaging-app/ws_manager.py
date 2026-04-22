from fastapi import WebSocket
from collections import defaultdict
from typing import Dict, List


class ConnectionManager:
    """Manages active WebSocket connections per conversation."""

    def __init__(self):
        self.active: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[conversation_id].append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        self.active[conversation_id].remove(websocket)

    async def broadcast(self, conversation_id: int, message: str):
        dead = []
        for ws in self.active[conversation_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active[conversation_id].remove(ws)


manager = ConnectionManager()
