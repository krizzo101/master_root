"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.project_connections: Dict[str, List[str]] = {}
        self.run_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket client connected", client_id=client_id)

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from project subscriptions
        for project_id, clients in self.project_connections.items():
            if client_id in clients:
                clients.remove(client_id)

        # Remove from run subscriptions
        for run_id, clients in self.run_connections.items():
            if client_id in clients:
                clients.remove(client_id)

        logger.info("WebSocket client disconnected", client_id=client_id)

    async def send_personal_message(
        self, message: Dict[str, Any], client_id: str
    ) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(
                    "Failed to send personal message", client_id=client_id, error=str(e)
                )
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(
                    "Failed to broadcast message", client_id=client_id, error=str(e)
                )
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def broadcast_to_project(
        self, project_id: str, message: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all clients subscribed to a project."""
        if project_id not in self.project_connections:
            return

        disconnected_clients = []

        for client_id in self.project_connections[project_id]:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(
                        json.dumps(message)
                    )
                except Exception as e:
                    logger.error(
                        "Failed to broadcast to project",
                        client_id=client_id,
                        project_id=project_id,
                        error=str(e),
                    )
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def broadcast_to_run(self, run_id: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all clients subscribed to a run."""
        if run_id not in self.run_connections:
            return

        disconnected_clients = []

        for client_id in self.run_connections[run_id]:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(
                        json.dumps(message)
                    )
                except Exception as e:
                    logger.error(
                        "Failed to broadcast to run",
                        client_id=client_id,
                        run_id=run_id,
                        error=str(e),
                    )
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def subscribe_to_project(self, client_id: str, project_id: str) -> None:
        """Subscribe a client to project updates."""
        if project_id not in self.project_connections:
            self.project_connections[project_id] = []

        if client_id not in self.project_connections[project_id]:
            self.project_connections[project_id].append(client_id)
            logger.info(
                "Client subscribed to project",
                client_id=client_id,
                project_id=project_id,
            )

    def subscribe_to_run(self, client_id: str, run_id: str) -> None:
        """Subscribe a client to run updates."""
        if run_id not in self.run_connections:
            self.run_connections[run_id] = []

        if client_id not in self.run_connections[run_id]:
            self.run_connections[run_id].append(client_id)
            logger.info("Client subscribed to run", client_id=client_id, run_id=run_id)

    def unsubscribe_from_project(self, client_id: str, project_id: str) -> None:
        """Unsubscribe a client from project updates."""
        if project_id in self.project_connections:
            if client_id in self.project_connections[project_id]:
                self.project_connections[project_id].remove(client_id)
                logger.info(
                    "Client unsubscribed from project",
                    client_id=client_id,
                    project_id=project_id,
                )

    def unsubscribe_from_run(self, client_id: str, run_id: str) -> None:
        """Unsubscribe a client from run updates."""
        if run_id in self.run_connections:
            if client_id in self.run_connections[run_id]:
                self.run_connections[run_id].remove(client_id)
                logger.info(
                    "Client unsubscribed from run", client_id=client_id, run_id=run_id
                )

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_project_subscribers(self, project_id: str) -> List[str]:
        """Get list of clients subscribed to a project."""
        return self.project_connections.get(project_id, [])

    def get_run_subscribers(self, run_id: str) -> List[str]:
        """Get list of clients subscribed to a run."""
        return self.run_connections.get(run_id, [])


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
