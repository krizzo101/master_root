import asyncio
import logging

from fastapi import WebSocket


class WebSocketManager:
    """Manages connected WebSocket clients and broadcasts events."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logging.getLogger("websocket").info(f"Client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logging.getLogger("websocket").info(
                f"Client disconnected: {websocket.client}"
            )
        except KeyError:
            pass

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        disconnects = []
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception as exc:
                logging.getLogger("websocket").error(f"Failed to send update: {exc}")
                disconnects.append(ws)
        for ws in disconnects:
            self.disconnect(ws)


# Singleton to import everywhere
ws_manager = WebSocketManager()
