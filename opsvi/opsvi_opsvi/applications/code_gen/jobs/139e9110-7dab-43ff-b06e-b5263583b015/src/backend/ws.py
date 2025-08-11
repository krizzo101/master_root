"""
WebSocket manager (Socket.IO-compatible) for FastAPI, providing real-time events for task updates, comments, assignment, deadline warnings.
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.websockets import WebSocketState
from backend.auth import get_current_user
from backend.models import User
import logging
from typing import Dict, Set

logger = logging.getLogger("taskmgmt.ws")
ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(project_id, set()).add(websocket)
        logger.info(f"WS Connect: {websocket.client} in {project_id}")

    async def disconnect(self, project_id: str, websocket: WebSocket):
        sockets = self.active_connections.get(project_id, set())
        if websocket in sockets:
            sockets.remove(websocket)

    async def broadcast(self, project_id: str, message: dict):
        for ws in self.active_connections.get(project_id, set()):
            if ws.application_state == WebSocketState.CONNECTED:
                await ws.send_json(message)


manager = ConnectionManager()


@ws_router.websocket("/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(project_id, {"event": "message", "data": data})
    except WebSocketDisconnect:
        await manager.disconnect(project_id, websocket)
