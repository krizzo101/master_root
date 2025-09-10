#!/usr/bin/env python3
"""
WebSocket Handler for IDE Context Bridge

Manages WebSocket connections and real-time communication with IDEs.
"""

import asyncio
import json
import logging
import uuid
import weakref
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

from .context_manager import ContextManager
from .models import (
    BridgeResponse,
    ConnectionRegistration,
    IDEContextMessage,
    SearchRequest,
    SuggestionRequest,
    WebSocketMessage,
)
from .suggestion_engine import SuggestionEngine

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents an individual WebSocket connection."""

    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.session_id: Optional[str] = None
        self.editor_id: Optional[str] = None
        self.subscriptions: Set[str] = set()
        self.connected_at = datetime.now()
        self.last_message_at = datetime.now()
        self.message_count = 0
        self.is_authenticated = False

    async def send_message(self, message: Dict[str, Any]):
        """Send message to client."""
        try:
            await self.websocket.send_text(json.dumps(message))
            self.last_message_at = datetime.now()
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            raise

    async def send_response(self, response: BridgeResponse):
        """Send typed response to client."""
        response_dict = response.dict()
        # Convert datetime to ISO string
        if response_dict.get("timestamp"):
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()

        await self.send_message(response_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection info to dictionary."""
        return {
            "connection_id": self.connection_id,
            "session_id": self.session_id,
            "editor_id": self.editor_id,
            "subscriptions": list(self.subscriptions),
            "connected_at": self.connected_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat(),
            "message_count": self.message_count,
            "is_authenticated": self.is_authenticated,
        }


class ConnectionManager:
    """Manages WebSocket connections and messaging."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.session_connections: Dict[
            str, Set[str]
        ] = {}  # session_id -> connection_ids
        self.subscription_map: Dict[str, Set[str]] = {}  # event_type -> connection_ids

    def add_connection(self, websocket: WebSocket) -> WebSocketConnection:
        """Add new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(websocket, connection_id)
        self.active_connections[connection_id] = connection

        logger.info(f"New WebSocket connection: {connection_id}")
        return connection

    def remove_connection(self, connection_id: str):
        """Remove WebSocket connection."""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]

            # Remove from session mapping
            if connection.session_id:
                if connection.session_id in self.session_connections:
                    self.session_connections[connection.session_id].discard(
                        connection_id
                    )
                    if not self.session_connections[connection.session_id]:
                        del self.session_connections[connection.session_id]

            # Remove from subscriptions
            for event_type in connection.subscriptions:
                if event_type in self.subscription_map:
                    self.subscription_map[event_type].discard(connection_id)
                    if not self.subscription_map[event_type]:
                        del self.subscription_map[event_type]

            del self.active_connections[connection_id]
            logger.info(f"Removed WebSocket connection: {connection_id}")

    def register_session(self, connection_id: str, session_id: str):
        """Register connection with session."""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            connection.session_id = session_id

            # Add to session mapping
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)

            logger.info(
                f"Registered connection {connection_id} with session {session_id}"
            )

    def subscribe_to_events(self, connection_id: str, event_types: List[str]):
        """Subscribe connection to specific event types."""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]

            for event_type in event_types:
                connection.subscriptions.add(event_type)

                if event_type not in self.subscription_map:
                    self.subscription_map[event_type] = set()
                self.subscription_map[event_type].add(connection_id)

            logger.info(f"Connection {connection_id} subscribed to: {event_types}")

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_message(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {e}")
                self.remove_connection(connection_id)
                return False
        return False

    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """Send message to all connections in a session."""
        sent_count = 0
        if session_id in self.session_connections:
            connection_ids = list(
                self.session_connections[session_id]
            )  # Copy to avoid modification during iteration

            for connection_id in connection_ids:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1

        return sent_count

    async def broadcast_to_subscribers(
        self, event_type: str, message: Dict[str, Any]
    ) -> int:
        """Broadcast message to all subscribers of an event type."""
        sent_count = 0
        if event_type in self.subscription_map:
            connection_ids = list(
                self.subscription_map[event_type]
            )  # Copy to avoid modification during iteration

            for connection_id in connection_ids:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1

        return sent_count

    async def disconnect_all(self):
        """Disconnect all WebSocket connections."""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            try:
                connection = self.active_connections[connection_id]
                await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
            finally:
                self.remove_connection(connection_id)

        logger.info("All WebSocket connections disconnected")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "active_sessions": len(self.session_connections),
            "subscription_types": len(self.subscription_map),
            "connections_per_session": {
                session_id: len(conn_ids)
                for session_id, conn_ids in self.session_connections.items()
            },
        }


class WebSocketHandler:
    """Handles WebSocket communication and message processing."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        context_manager: ContextManager,
        suggestion_engine: SuggestionEngine,
        redis_client: Optional[redis.Redis] = None,
    ):
        self.connection_manager = connection_manager
        self.context_manager = context_manager
        self.suggestion_engine = suggestion_engine
        self.redis_client = redis_client

        # Message handlers
        self.message_handlers = {
            "register": self._handle_registration,
            "context_update": self._handle_context_update,
            "query_request": self._handle_query_request,
            "suggestion_request": self._handle_suggestion_request,
            "subscribe": self._handle_subscription,
            "ping": self._handle_ping,
        }

    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        connection = self.connection_manager.add_connection(websocket)

        try:
            # Send welcome message
            await connection.send_message(
                {
                    "type": "welcome",
                    "connection_id": connection.connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Connected to IDE Context Bridge",
                }
            )

            # Message processing loop
            while True:
                # Receive message
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    connection.message_count += 1
                    connection.last_message_at = datetime.now()

                    await self._process_message(connection, message)

                except json.JSONDecodeError as e:
                    await connection.send_message(
                        {
                            "type": "error",
                            "error": {
                                "code": "INVALID_JSON",
                                "message": f"Invalid JSON: {str(e)}",
                            },
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing message from {connection.connection_id}: {e}"
                    )
                    await connection.send_message(
                        {
                            "type": "error",
                            "error": {
                                "code": "PROCESSING_ERROR",
                                "message": "Internal error processing message",
                            },
                        }
                    )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection.connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connection_manager.remove_connection(connection.connection_id)

    async def _process_message(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Process incoming message."""
        message_type = message.get("type")
        if not message_type:
            await connection.send_message(
                {
                    "type": "error",
                    "error": {
                        "code": "MISSING_TYPE",
                        "message": "Message must have a 'type' field",
                    },
                }
            )
            return

        # Get handler
        handler = self.message_handlers.get(message_type)
        if not handler:
            await connection.send_message(
                {
                    "type": "error",
                    "error": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {message_type}",
                    },
                }
            )
            return

        try:
            await handler(connection, message)
        except Exception as e:
            logger.error(f"Handler error for {message_type}: {e}")
            await connection.send_message(
                {
                    "type": "error",
                    "error": {
                        "code": "HANDLER_ERROR",
                        "message": "Error processing message",
                    },
                }
            )

    async def _handle_registration(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle connection registration."""
        try:
            data = message.get("data", {})
            registration = ConnectionRegistration(**data)

            # Set connection info
            connection.session_id = registration.session_id
            connection.editor_id = registration.editor_id
            connection.is_authenticated = True  # TODO: Implement proper auth

            # Register with manager
            self.connection_manager.register_session(
                connection.connection_id, registration.session_id
            )

            # Subscribe to events
            if registration.subscriptions:
                self.connection_manager.subscribe_to_events(
                    connection.connection_id, registration.subscriptions
                )

            # Send confirmation
            await connection.send_response(
                BridgeResponse(
                    type="context_ack",
                    session_id=registration.session_id,
                    data={
                        "status": "registered",
                        "connection_id": connection.connection_id,
                        "subscriptions": registration.subscriptions,
                    },
                )
            )

            logger.info(
                f"Registered connection {connection.connection_id} for session {registration.session_id}"
            )

        except Exception as e:
            await connection.send_response(
                BridgeResponse(
                    type="error",
                    session_id=connection.session_id or "unknown",
                    error={"code": "REGISTRATION_FAILED", "message": str(e)},
                )
            )

    async def _handle_context_update(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle IDE context update."""
        try:
            # Parse context message
            context_msg = IDEContextMessage(**message)

            # Update context
            success = await self.context_manager.update_context(
                session_id=context_msg.session_id, context_data=message
            )

            if success:
                # Send acknowledgment
                await connection.send_response(
                    BridgeResponse(
                        type="context_ack",
                        session_id=context_msg.session_id,
                        data={"status": "updated"},
                    )
                )

                # Broadcast update to other connections in session
                update_notification = {
                    "type": "context_updated",
                    "session_id": context_msg.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "active_file": context_msg.active_file.path
                    if context_msg.active_file
                    else None,
                }

                await self.connection_manager.send_to_session(
                    context_msg.session_id, update_notification
                )

                # Publish to Redis if available
                if self.redis_client:
                    await self.redis_client.publish(
                        f"context:updates:{context_msg.session_id}",
                        json.dumps(update_notification),
                    )

            else:
                await connection.send_response(
                    BridgeResponse(
                        type="error",
                        session_id=context_msg.session_id,
                        error={
                            "code": "CONTEXT_UPDATE_FAILED",
                            "message": "Failed to update context",
                        },
                    )
                )

        except Exception as e:
            logger.error(f"Context update error: {e}")
            await connection.send_response(
                BridgeResponse(
                    type="error",
                    session_id=connection.session_id or "unknown",
                    error={"code": "CONTEXT_UPDATE_ERROR", "message": str(e)},
                )
            )

    async def _handle_query_request(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle search query request."""
        try:
            data = message.get("data", {})
            search_req = SearchRequest(
                session_id=connection.session_id or "unknown", **data
            )

            # Perform search
            results = await self.suggestion_engine.search_context(
                query=search_req.query,
                search_type=search_req.type,
                filters=search_req.filters,
                max_results=search_req.max_results or 10,
            )

            # Send results
            await connection.send_response(
                BridgeResponse(
                    type="search_results",
                    request_id=search_req.request_id,
                    session_id=search_req.session_id,
                    data={
                        "search_results": [result.dict() for result in results],
                        "result_count": len(results),
                    },
                )
            )

        except Exception as e:
            logger.error(f"Query request error: {e}")
            await connection.send_response(
                BridgeResponse(
                    type="error",
                    session_id=connection.session_id or "unknown",
                    error={"code": "QUERY_ERROR", "message": str(e)},
                )
            )

    async def _handle_suggestion_request(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle suggestion request."""
        try:
            data = message.get("data", {})
            suggestion_req = SuggestionRequest(
                session_id=connection.session_id or "unknown", **data
            )

            # Generate suggestions
            suggestions = await self.suggestion_engine.generate_suggestions(
                session_id=suggestion_req.session_id,
                file_path=suggestion_req.file_path,
                cursor_position=suggestion_req.cursor_position,
                context=suggestion_req.context,
                suggestion_types=suggestion_req.types,
            )

            # Send suggestions
            await connection.send_response(
                BridgeResponse(
                    type="suggestions",
                    request_id=suggestion_req.request_id,
                    session_id=suggestion_req.session_id,
                    data={
                        "suggestions": [
                            suggestion.dict() for suggestion in suggestions
                        ],
                        "suggestion_count": len(suggestions),
                    },
                )
            )

        except Exception as e:
            logger.error(f"Suggestion request error: {e}")
            await connection.send_response(
                BridgeResponse(
                    type="error",
                    session_id=connection.session_id or "unknown",
                    error={"code": "SUGGESTION_ERROR", "message": str(e)},
                )
            )

    async def _handle_subscription(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle event subscription."""
        try:
            event_types = message.get("data", {}).get("events", [])

            self.connection_manager.subscribe_to_events(
                connection.connection_id, event_types
            )

            await connection.send_message(
                {
                    "type": "subscription_ack",
                    "data": {
                        "subscribed_events": event_types,
                        "total_subscriptions": len(connection.subscriptions),
                    },
                }
            )

        except Exception as e:
            await connection.send_message(
                {
                    "type": "error",
                    "error": {"code": "SUBSCRIPTION_ERROR", "message": str(e)},
                }
            )

    async def _handle_ping(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle ping message."""
        await connection.send_message(
            {
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
                "connection_id": connection.connection_id,
            }
        )

    async def broadcast_suggestion(
        self, session_id: str, suggestions: List[Dict[str, Any]]
    ):
        """Broadcast suggestions to all connections in a session."""
        message = {
            "type": "suggestions_broadcast",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "suggestions": suggestions,
        }

        await self.connection_manager.send_to_session(session_id, message)

        # Also broadcast to subscribers
        await self.connection_manager.broadcast_to_subscribers("suggestions", message)

    async def broadcast_context_change(
        self, session_id: str, context_summary: Dict[str, Any]
    ):
        """Broadcast context changes to subscribers."""
        message = {
            "type": "context_change",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "context": context_summary,
        }

        await self.connection_manager.broadcast_to_subscribers(
            "context_changes", message
        )

    def get_handler_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "connection_stats": self.connection_manager.get_connection_stats(),
            "active_handlers": list(self.message_handlers.keys()),
            "redis_available": self.redis_client is not None,
        }
