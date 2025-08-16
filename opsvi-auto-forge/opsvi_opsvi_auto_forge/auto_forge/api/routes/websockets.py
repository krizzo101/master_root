"""WebSocket routes for real-time updates."""

import json
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel
import structlog

from ..websocket_manager import websocket_manager
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

logger = structlog.get_logger()
router = APIRouter()


class WebSocketMessage(BaseModel):
    """WebSocket message model."""

    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None


class SubscriptionRequest(BaseModel):
    """Subscription request model."""

    action: str  # "subscribe" or "unsubscribe"
    resource_type: str  # "project" or "run"
    resource_id: str


async def get_neo4j_client() -> Neo4jClient:
    """Dependency to get Neo4j client."""
    # This would be injected from the main app
    from ..main import neo4j_client

    return neo4j_client


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
):
    """Main WebSocket endpoint for real-time updates."""
    if not client_id:
        client_id = str(uuid.uuid4())

    await websocket_manager.connect(websocket, client_id)

    # Auto-subscribe to project/run if provided
    if project_id:
        websocket_manager.subscribe_to_project(client_id, project_id)
    if run_id:
        websocket_manager.subscribe_to_run(client_id, run_id)

    try:
        # Send welcome message
        await websocket_manager.send_personal_message(
            {
                "type": "connection_established",
                "data": {
                    "client_id": client_id,
                    "message": "Connected to Autonomous Software Factory",
                    "subscriptions": {"project": project_id, "run": run_id},
                },
            },
            client_id,
        )

        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle subscription requests
                if message.get("type") == "subscription":
                    await handle_subscription_request(client_id, message)

                # Handle ping/pong
                elif message.get("type") == "ping":
                    await websocket_manager.send_personal_message(
                        {
                            "type": "pong",
                            "data": {"timestamp": message.get("timestamp")},
                        },
                        client_id,
                    )

                # Handle status request
                elif message.get("type") == "status":
                    await handle_status_request(client_id)

                else:
                    # Echo back unknown message types
                    await websocket_manager.send_personal_message(
                        {
                            "type": "error",
                            "data": {
                                "message": f"Unknown message type: {message.get('type')}",
                                "received": message,
                            },
                        },
                        client_id,
                    )

            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    {"type": "error", "data": {"message": "Invalid JSON format"}},
                    client_id,
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info("WebSocket client disconnected", client_id=client_id)


async def handle_subscription_request(client_id: str, message: Dict[str, Any]) -> None:
    """Handle subscription/unsubscription requests."""
    try:
        request = SubscriptionRequest(**message.get("data", {}))

        if request.action == "subscribe":
            if request.resource_type == "project":
                websocket_manager.subscribe_to_project(client_id, request.resource_id)
                await websocket_manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "data": {
                            "resource_type": "project",
                            "resource_id": request.resource_id,
                            "status": "subscribed",
                        },
                    },
                    client_id,
                )

            elif request.resource_type == "run":
                websocket_manager.subscribe_to_run(client_id, request.resource_id)
                await websocket_manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "data": {
                            "resource_type": "run",
                            "resource_id": request.resource_id,
                            "status": "subscribed",
                        },
                    },
                    client_id,
                )

        elif request.action == "unsubscribe":
            if request.resource_type == "project":
                websocket_manager.unsubscribe_from_project(
                    client_id, request.resource_id
                )
                await websocket_manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "data": {
                            "resource_type": "project",
                            "resource_id": request.resource_id,
                            "status": "unsubscribed",
                        },
                    },
                    client_id,
                )

            elif request.resource_type == "run":
                websocket_manager.unsubscribe_from_run(client_id, request.resource_id)
                await websocket_manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "data": {
                            "resource_type": "run",
                            "resource_id": request.resource_id,
                            "status": "unsubscribed",
                        },
                    },
                    client_id,
                )

    except Exception as e:
        await websocket_manager.send_personal_message(
            {
                "type": "error",
                "data": {"message": f"Failed to handle subscription request: {str(e)}"},
            },
            client_id,
        )


async def handle_status_request(client_id: str) -> None:
    """Handle status request."""
    try:
        # Get connection status
        connection_count = websocket_manager.get_connection_count()

        # Get client's subscriptions
        project_subscriptions = []
        run_subscriptions = []

        for project_id, clients in websocket_manager.project_connections.items():
            if client_id in clients:
                project_subscriptions.append(project_id)

        for run_id, clients in websocket_manager.run_connections.items():
            if client_id in clients:
                run_subscriptions.append(run_id)

        await websocket_manager.send_personal_message(
            {
                "type": "status",
                "data": {
                    "client_id": client_id,
                    "total_connections": connection_count,
                    "subscriptions": {
                        "projects": project_subscriptions,
                        "runs": run_subscriptions,
                    },
                },
            },
            client_id,
        )

    except Exception as e:
        await websocket_manager.send_personal_message(
            {"type": "error", "data": {"message": f"Failed to get status: {str(e)}"}},
            client_id,
        )


# Event broadcasting functions for use by other parts of the system


async def broadcast_project_update(
    project_id: str, event_type: str, data: Dict[str, Any]
) -> None:
    """Broadcast a project update to all subscribed clients."""
    message = {
        "type": f"project_{event_type}",
        "data": {"project_id": project_id, **data},
    }
    await websocket_manager.broadcast_to_project(project_id, message)


async def broadcast_run_update(
    run_id: str, event_type: str, data: Dict[str, Any]
) -> None:
    """Broadcast a run update to all subscribed clients."""
    message = {"type": f"run_{event_type}", "data": {"run_id": run_id, **data}}
    await websocket_manager.broadcast_to_run(run_id, message)


async def broadcast_task_update(
    run_id: str, task_id: str, event_type: str, data: Dict[str, Any]
) -> None:
    """Broadcast a task update to all clients subscribed to the run."""
    message = {
        "type": f"task_{event_type}",
        "data": {"run_id": run_id, "task_id": task_id, **data},
    }
    await websocket_manager.broadcast_to_run(run_id, message)


async def broadcast_system_event(event_type: str, data: Dict[str, Any]) -> None:
    """Broadcast a system-wide event to all connected clients."""
    message = {"type": f"system_{event_type}", "data": data}
    await websocket_manager.broadcast(message)
