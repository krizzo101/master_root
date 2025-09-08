#!/usr/bin/env python3
"""
Sync Engine - Real-time synchronization across agents

This module provides the SyncEngine class which handles:
- Real-time file synchronization between agents
- WebSocket-based notifications for changes
- Event broadcasting and subscription
- Operational Transform for collaborative editing
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol

from .change_tracker import ChangeTracker


@dataclass
class SyncEvent:
    """Represents a synchronization event"""

    event_id: str
    event_type: str  # file_changed, agent_joined, agent_left, etc.
    workspace_id: str
    resource_path: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConnection:
    """Represents a connected agent"""

    agent_id: str
    websocket: WebSocketServerProtocol
    workspace_ids: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)


@dataclass
class OperationalTransform:
    """Operational Transform for collaborative editing"""

    operation_id: str
    operation_type: str  # insert, delete, retain
    position: int
    content: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    document_version: int = 0


class SyncEngine:
    """
    Real-time synchronization engine for collaborative workspaces

    Provides WebSocket-based real-time synchronization, event broadcasting,
    and operational transforms for collaborative editing.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        change_tracker: Optional[ChangeTracker] = None,
    ):
        self.host = host
        self.port = port
        self.change_tracker = change_tracker

        # Connected agents
        self.agents: Dict[str, AgentConnection] = {}
        self.workspace_subscriptions: Dict[
            str, Set[str]
        ] = {}  # workspace_id -> agent_ids

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Operational Transform state
        self.document_versions: Dict[str, int] = {}  # file_path -> version
        self.pending_operations: Dict[
            str, List[OperationalTransform]
        ] = {}  # file_path -> ops

        # Thread safety
        self.lock = asyncio.Lock()

        # Server instance
        self.server = None

    async def start_server(self):
        """Start the WebSocket sync server"""
        self.server = await websockets.serve(
            self.handle_connection, self.host, self.port
        )
        print(f"Sync engine started on ws://{self.host}:{self.port}")

    async def stop_server(self):
        """Stop the WebSocket sync server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection"""
        agent_id = None

        try:
            # Wait for agent identification
            async for message in websocket:
                try:
                    data = json.loads(message)

                    if data.get("type") == "identify" and not agent_id:
                        agent_id = data.get("agent_id")
                        if agent_id:
                            await self._register_agent(agent_id, websocket)
                            await self._send_to_agent(
                                agent_id,
                                {
                                    "type": "identified",
                                    "agent_id": agent_id,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )

                    elif agent_id:
                        await self._handle_agent_message(agent_id, data)

                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({"type": "error", "message": "Invalid JSON format"})
                    )
                except Exception as e:
                    await websocket.send(
                        json.dumps({"type": "error", "message": str(e)})
                    )

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:
            if agent_id:
                await self._unregister_agent(agent_id)

    async def _register_agent(self, agent_id: str, websocket: WebSocketServerProtocol):
        """Register a new agent connection"""
        async with self.lock:
            connection = AgentConnection(agent_id=agent_id, websocket=websocket)
            self.agents[agent_id] = connection

            # Broadcast agent joined event
            await self._broadcast_event(
                SyncEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="agent_joined",
                    workspace_id="system",
                    resource_path="",
                    agent_id=agent_id,
                    data={"agent_id": agent_id},
                )
            )

    async def _unregister_agent(self, agent_id: str):
        """Unregister an agent connection"""
        async with self.lock:
            connection = self.agents.get(agent_id)
            if not connection:
                return

            # Remove from workspace subscriptions
            for workspace_id in connection.workspace_ids:
                if workspace_id in self.workspace_subscriptions:
                    self.workspace_subscriptions[workspace_id].discard(agent_id)
                    if not self.workspace_subscriptions[workspace_id]:
                        del self.workspace_subscriptions[workspace_id]

            # Remove connection
            del self.agents[agent_id]

            # Broadcast agent left event
            await self._broadcast_event(
                SyncEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="agent_left",
                    workspace_id="system",
                    resource_path="",
                    agent_id=agent_id,
                    data={"agent_id": agent_id},
                )
            )

    async def _handle_agent_message(self, agent_id: str, message: Dict[str, Any]):
        """Handle a message from an agent"""
        message_type = message.get("type")

        if message_type == "subscribe_workspace":
            workspace_id = message.get("workspace_id")
            if workspace_id:
                await self._subscribe_agent_to_workspace(agent_id, workspace_id)

        elif message_type == "unsubscribe_workspace":
            workspace_id = message.get("workspace_id")
            if workspace_id:
                await self._unsubscribe_agent_from_workspace(agent_id, workspace_id)

        elif message_type == "file_changed":
            await self._handle_file_change(agent_id, message)

        elif message_type == "operational_transform":
            await self._handle_operational_transform(agent_id, message)

        elif message_type == "ping":
            await self._handle_ping(agent_id)

        else:
            await self._send_to_agent(
                agent_id,
                {"type": "error", "message": f"Unknown message type: {message_type}"},
            )

    async def _subscribe_agent_to_workspace(self, agent_id: str, workspace_id: str):
        """Subscribe agent to workspace events"""
        async with self.lock:
            connection = self.agents.get(agent_id)
            if not connection:
                return

            connection.workspace_ids.add(workspace_id)

            if workspace_id not in self.workspace_subscriptions:
                self.workspace_subscriptions[workspace_id] = set()

            self.workspace_subscriptions[workspace_id].add(agent_id)

            await self._send_to_agent(
                agent_id,
                {
                    "type": "subscribed",
                    "workspace_id": workspace_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _unsubscribe_agent_from_workspace(self, agent_id: str, workspace_id: str):
        """Unsubscribe agent from workspace events"""
        async with self.lock:
            connection = self.agents.get(agent_id)
            if connection:
                connection.workspace_ids.discard(workspace_id)

            if workspace_id in self.workspace_subscriptions:
                self.workspace_subscriptions[workspace_id].discard(agent_id)
                if not self.workspace_subscriptions[workspace_id]:
                    del self.workspace_subscriptions[workspace_id]

            await self._send_to_agent(
                agent_id,
                {
                    "type": "unsubscribed",
                    "workspace_id": workspace_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _handle_file_change(self, agent_id: str, message: Dict[str, Any]):
        """Handle file change notification"""
        workspace_id = message.get("workspace_id")
        file_path = message.get("file_path")
        change_type = message.get("change_type")

        if not all([workspace_id, file_path, change_type]):
            return

        # Create sync event
        event = SyncEvent(
            event_id=str(uuid.uuid4()),
            event_type="file_changed",
            workspace_id=workspace_id,
            resource_path=file_path,
            agent_id=agent_id,
            data={
                "change_type": change_type,
                "file_path": file_path,
                **message.get("metadata", {}),
            },
        )

        # Broadcast to workspace subscribers
        await self._broadcast_to_workspace(workspace_id, event, exclude_agent=agent_id)

        # Track the change
        if self.change_tracker:
            await self.change_tracker.track_file_event(
                file_path, change_type, message.get("metadata", {}), agent_id
            )

    async def _handle_operational_transform(
        self, agent_id: str, message: Dict[str, Any]
    ):
        """Handle operational transform operation"""
        file_path = message.get("file_path")
        operation = message.get("operation")

        if not all([file_path, operation]):
            return

        # Create operational transform
        transform = OperationalTransform(
            operation_id=str(uuid.uuid4()),
            operation_type=operation.get("type"),
            position=operation.get("position", 0),
            content=operation.get("content", ""),
            agent_id=agent_id,
            document_version=operation.get("document_version", 0),
        )

        # Apply operational transform
        await self._apply_operational_transform(file_path, transform)

    async def _apply_operational_transform(
        self, file_path: str, transform: OperationalTransform
    ):
        """Apply operational transform to document"""
        async with self.lock:
            current_version = self.document_versions.get(file_path, 0)

            # Add to pending operations
            if file_path not in self.pending_operations:
                self.pending_operations[file_path] = []

            self.pending_operations[file_path].append(transform)

            # Transform operations against each other
            transformed_ops = await self._transform_operations(file_path)

            # Broadcast transformed operations
            for workspace_id in self.workspace_subscriptions:
                await self._broadcast_to_workspace(
                    workspace_id,
                    SyncEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="operational_transform",
                        workspace_id=workspace_id,
                        resource_path=file_path,
                        agent_id=transform.agent_id,
                        data={
                            "operations": [asdict(op) for op in transformed_ops],
                            "document_version": current_version + 1,
                        },
                    ),
                    exclude_agent=transform.agent_id,
                )

            # Update document version
            self.document_versions[file_path] = current_version + 1

            # Clear processed operations
            self.pending_operations[file_path] = []

    async def _transform_operations(self, file_path: str) -> List[OperationalTransform]:
        """Transform operations to resolve conflicts"""
        operations = self.pending_operations.get(file_path, [])

        if len(operations) <= 1:
            return operations

        # Sort operations by timestamp
        operations.sort(key=lambda op: op.timestamp)

        # Apply operational transform algorithm
        transformed = []
        for i, op in enumerate(operations):
            transformed_op = op

            # Transform against all previous operations
            for prev_op in operations[:i]:
                transformed_op = self._transform_operation_pair(transformed_op, prev_op)

            transformed.append(transformed_op)

        return transformed

    def _transform_operation_pair(
        self, op1: OperationalTransform, op2: OperationalTransform
    ) -> OperationalTransform:
        """Transform one operation against another"""
        # Basic operational transform logic
        # This is a simplified version - a full implementation would be more complex

        if op1.operation_type == "insert" and op2.operation_type == "insert":
            if op1.position <= op2.position:
                # op1 comes before op2, adjust op2's position
                return OperationalTransform(
                    operation_id=op1.operation_id,
                    operation_type=op1.operation_type,
                    position=op1.position,
                    content=op1.content,
                    agent_id=op1.agent_id,
                    timestamp=op1.timestamp,
                    document_version=op1.document_version,
                )
            else:
                # op2 comes before op1, adjust op1's position
                return OperationalTransform(
                    operation_id=op1.operation_id,
                    operation_type=op1.operation_type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    agent_id=op1.agent_id,
                    timestamp=op1.timestamp,
                    document_version=op1.document_version,
                )

        elif op1.operation_type == "delete" and op2.operation_type == "insert":
            if op1.position <= op2.position:
                return OperationalTransform(
                    operation_id=op1.operation_id,
                    operation_type=op1.operation_type,
                    position=op1.position,
                    content=op1.content,
                    agent_id=op1.agent_id,
                    timestamp=op1.timestamp,
                    document_version=op1.document_version,
                )
            else:
                return OperationalTransform(
                    operation_id=op1.operation_id,
                    operation_type=op1.operation_type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    agent_id=op1.agent_id,
                    timestamp=op1.timestamp,
                    document_version=op1.document_version,
                )

        # Return original operation if no transformation needed
        return op1

    async def _handle_ping(self, agent_id: str):
        """Handle ping from agent"""
        connection = self.agents.get(agent_id)
        if connection:
            connection.last_ping = datetime.now()
            await self._send_to_agent(
                agent_id, {"type": "pong", "timestamp": datetime.now().isoformat()}
            )

    async def _broadcast_event(self, event: SyncEvent):
        """Broadcast event to all connected agents"""
        event_data = asdict(event)
        event_data["timestamp"] = event.timestamp.isoformat()

        message = {"type": "sync_event", "event": event_data}

        # Send to all connected agents
        disconnected_agents = []
        for agent_id, connection in self.agents.items():
            try:
                await connection.websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_agents.append(agent_id)

        # Clean up disconnected agents
        for agent_id in disconnected_agents:
            await self._unregister_agent(agent_id)

    async def _broadcast_to_workspace(
        self, workspace_id: str, event: SyncEvent, exclude_agent: Optional[str] = None
    ):
        """Broadcast event to agents subscribed to a workspace"""
        if workspace_id not in self.workspace_subscriptions:
            return

        event_data = asdict(event)
        event_data["timestamp"] = event.timestamp.isoformat()

        message = {"type": "sync_event", "event": event_data}

        # Send to subscribed agents
        disconnected_agents = []
        for agent_id in self.workspace_subscriptions[workspace_id]:
            if exclude_agent and agent_id == exclude_agent:
                continue

            connection = self.agents.get(agent_id)
            if connection:
                try:
                    await connection.websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_agents.append(agent_id)

        # Clean up disconnected agents
        for agent_id in disconnected_agents:
            await self._unregister_agent(agent_id)

    async def _send_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Send message to a specific agent"""
        connection = self.agents.get(agent_id)
        if connection:
            try:
                await connection.websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                await self._unregister_agent(agent_id)

    # Public API methods
    async def broadcast_file_change(
        self,
        workspace_id: str,
        file_path: str,
        change_type: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Broadcast a file change event"""
        event = SyncEvent(
            event_id=str(uuid.uuid4()),
            event_type="file_changed",
            workspace_id=workspace_id,
            resource_path=file_path,
            agent_id=agent_id,
            data={
                "change_type": change_type,
                "file_path": file_path,
                **(metadata or {}),
            },
        )

        await self._broadcast_to_workspace(workspace_id, event, exclude_agent=agent_id)

    async def get_connected_agents(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of connected agents"""
        agents_info = []

        for agent_id, connection in self.agents.items():
            if workspace_id and workspace_id not in connection.workspace_ids:
                continue

            agents_info.append(
                {
                    "agent_id": agent_id,
                    "connected_at": connection.connected_at.isoformat(),
                    "last_ping": connection.last_ping.isoformat(),
                    "workspaces": list(connection.workspace_ids),
                }
            )

        return agents_info

    async def get_workspace_activity(self, workspace_id: str) -> Dict[str, Any]:
        """Get activity summary for a workspace"""
        subscribers = self.workspace_subscriptions.get(workspace_id, set())

        return {
            "workspace_id": workspace_id,
            "active_agents": len(subscribers),
            "agent_ids": list(subscribers),
            "last_activity": datetime.now().isoformat(),  # Would track actual last activity
        }

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register a handler for sync events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def trigger_event_handlers(self, event: SyncEvent):
        """Trigger registered event handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
