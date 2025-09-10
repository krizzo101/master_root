#!/usr/bin/env python3
"""
WebSocket Handler - Real-time communication for monitoring dashboard
Enhanced with improved connection management, heartbeat mechanism, and error recovery
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata"""

    def __init__(self, websocket: WebSocket, client_id: str = None):
        self.websocket = websocket
        self.client_id = client_id or str(uuid.uuid4())
        self.connected_at = time.time()
        self.last_ping = time.time()
        self.subscriptions: Set[str] = {"status", "tasks"}  # Default subscriptions
        self.is_alive = True
        self.reconnect_attempts = 0
        self.user_agent = None
        self.remote_addr = None

    def update_ping(self):
        """Update last ping time"""
        self.last_ping = time.time()

    def is_stale(self, timeout: int = 60) -> bool:
        """Check if connection is stale (no ping for timeout seconds)"""
        return time.time() - self.last_ping > timeout


class WebSocketManager:
    """Enhanced WebSocket manager with connection pooling, heartbeat, and error recovery"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.is_broadcasting = False
        self.broadcast_interval = 2  # seconds

        # Enhanced update frequencies for different data types
        self.update_frequencies = {
            "status": 3,  # System status every 3 seconds (reduced for better UX)
            "tasks": 7,  # Task list every 7 seconds (optimized for balance)
            "performance": 15,  # Performance metrics every 15 seconds
            "analytics": 30,  # Analytics every 30 seconds
            "logs": 2,  # Log updates every 2 seconds
            "quality": 60,  # Quality reports every minute
        }

        self.last_updates = {
            "status": 0,
            "tasks": 0,
            "performance": 0,
            "analytics": 0,
            "logs": 0,
            "quality": 0,
        }

        # Connection management settings
        self.heartbeat_interval = 30  # Send heartbeat every 30 seconds
        self.connection_timeout = 90  # Consider connection dead after 90 seconds
        self.max_connections = 100  # Maximum concurrent connections
        self.cleanup_interval = 60  # Clean up stale connections every 60 seconds

        # Statistics tracking
        self.stats = {
            "total_connections": 0,
            "reconnections": 0,
            "broadcasts_sent": 0,
            "errors": 0,
            "last_cleanup": time.time(),
        }

    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """Accept new WebSocket connection with enhanced connection management"""
        # Check connection limits
        if len(self.connections) >= self.max_connections:
            logger.warning(
                f"Connection limit reached ({self.max_connections}). Rejecting new connection."
            )
            await websocket.close(code=1013, reason="Server overloaded")
            return None

        await websocket.accept()

        # Create connection object
        connection = WebSocketConnection(websocket, client_id)

        # Extract client information if available
        try:
            client_host = websocket.client.host if websocket.client else "unknown"
            connection.remote_addr = client_host
            # Note: FastAPI WebSocket doesn't provide headers easily, so user_agent remains None
        except Exception:
            pass

        self.connections[connection.client_id] = connection
        self.stats["total_connections"] += 1

        logger.info(
            f"Client {connection.client_id} connected from {connection.remote_addr}. Total connections: {len(self.connections)}"
        )

        # Send initial data
        await self._send_initial_data(connection)

        return connection.client_id

    async def disconnect(self, client_id: str = None, websocket: WebSocket = None):
        """Remove WebSocket connection with enhanced cleanup"""
        connection = None

        if client_id and client_id in self.connections:
            connection = self.connections[client_id]
            del self.connections[client_id]
        elif websocket:
            # Find connection by websocket (fallback for compatibility)
            for cid, conn in self.connections.items():
                if conn.websocket == websocket:
                    connection = conn
                    del self.connections[cid]
                    break

        if connection:
            connection.is_alive = False
            logger.info(
                f"Client {connection.client_id} disconnected. Total connections: {len(self.connections)}"
            )
        else:
            logger.warning("Attempted to disconnect unknown connection")

    async def handle_subscription(self, websocket: WebSocket, message: Dict):
        """Handle subscription management from client with enhanced features"""
        try:
            subscription_type = message.get("subscription")
            action = message.get("action", "subscribe")  # subscribe/unsubscribe
            client_id = message.get("client_id")

            # Find connection
            connection = None
            if client_id and client_id in self.connections:
                connection = self.connections[client_id]
            else:
                # Fallback: find by websocket
                for conn in self.connections.values():
                    if conn.websocket == websocket:
                        connection = conn
                        break

            if not connection:
                logger.error("Could not find connection for subscription request")
                return

            if action == "subscribe":
                connection.subscriptions.add(subscription_type)
                await websocket.send_json(
                    {
                        "type": "subscription_confirmed",
                        "subscription": subscription_type,
                        "action": action,
                        "client_id": connection.client_id,
                    }
                )
                logger.info(
                    f"Client {connection.client_id} subscribed to {subscription_type}"
                )

            elif action == "unsubscribe":
                connection.subscriptions.discard(subscription_type)
                await websocket.send_json(
                    {
                        "type": "subscription_confirmed",
                        "subscription": subscription_type,
                        "action": action,
                        "client_id": connection.client_id,
                    }
                )
                logger.info(
                    f"Client {connection.client_id} unsubscribed from {subscription_type}"
                )

            elif action == "list_subscriptions":
                await websocket.send_json(
                    {
                        "type": "subscription_list",
                        "subscriptions": list(connection.subscriptions),
                        "client_id": connection.client_id,
                    }
                )

        except Exception as e:
            logger.error(f"Subscription handling error: {e}")
            self.stats["errors"] += 1

    async def broadcast_to_subscribers(self, data_type: str, data: Dict):
        """Enhanced broadcast with connection management and error recovery"""
        if not self.connections:
            return

        message = {
            "type": "update",
            "data_type": data_type,
            "data": data,
            "timestamp": time.time(),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        disconnected_clients = []
        successful_broadcasts = 0

        for client_id, connection in self.connections.items():
            # Skip if client not subscribed to this data type
            if data_type not in connection.subscriptions:
                continue

            # Skip if connection is not alive
            if not connection.is_alive:
                disconnected_clients.append(client_id)
                continue

            try:
                await connection.websocket.send_json(message)
                successful_broadcasts += 1

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected during broadcast")
                disconnected_clients.append(client_id)

            except Exception as e:
                logger.warning(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)
                self.stats["errors"] += 1

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

        # Update statistics
        self.stats["broadcasts_sent"] += successful_broadcasts

        if successful_broadcasts > 0:
            logger.debug(
                f"Broadcast {data_type}: {successful_broadcasts} clients, {len(disconnected_clients)} disconnected"
            )

    async def start_broadcast_loop(self):
        """Enhanced broadcast loop with heartbeat and connection management"""
        from monitoring_service import MonitoringService

        self.is_broadcasting = True
        monitoring_service = MonitoringService()

        logger.info("Starting enhanced WebSocket broadcast loop with heartbeat")

        # Start parallel tasks for different responsibilities
        tasks = [
            asyncio.create_task(self._data_broadcast_loop(monitoring_service)),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Broadcast loop system error: {e}")
        finally:
            for task in tasks:
                task.cancel()

    async def _data_broadcast_loop(self, monitoring_service):
        """Main data broadcasting loop"""
        while self.is_broadcasting:
            try:
                current_time = time.time()

                # Check which updates are due
                for data_type, frequency in self.update_frequencies.items():
                    if current_time - self.last_updates[data_type] >= frequency:
                        await self._broadcast_data_type(data_type, monitoring_service)
                        self.last_updates[data_type] = current_time

                await asyncio.sleep(0.5)  # Small sleep to prevent busy waiting

            except Exception as e:
                logger.error(f"Data broadcast loop error: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)

    async def _heartbeat_loop(self):
        """Heartbeat loop to check connection health"""
        while self.is_broadcasting:
            try:
                current_time = time.time()
                disconnected_clients = []

                for client_id, connection in self.connections.items():
                    try:
                        # Send heartbeat to all connections
                        await connection.websocket.send_json(
                            {
                                "type": "heartbeat",
                                "timestamp": current_time,
                                "client_id": client_id,
                                "server_uptime": current_time
                                - self.stats.get("start_time", current_time),
                            }
                        )
                        connection.update_ping()

                    except WebSocketDisconnect:
                        logger.info(f"Client {client_id} disconnected during heartbeat")
                        disconnected_clients.append(client_id)

                    except Exception as e:
                        logger.warning(f"Heartbeat failed for client {client_id}: {e}")
                        # Mark as stale, will be cleaned up in cleanup loop
                        connection.is_alive = False

                # Clean up disconnected clients
                for client_id in disconnected_clients:
                    await self.disconnect(client_id)

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(self.heartbeat_interval)

    async def _cleanup_loop(self):
        """Connection cleanup loop for stale connections"""
        while self.is_broadcasting:
            try:
                current_time = time.time()
                stale_clients = []

                # Find stale connections
                for client_id, connection in self.connections.items():
                    if (
                        connection.is_stale(self.connection_timeout)
                        or not connection.is_alive
                    ):
                        stale_clients.append(client_id)

                # Clean up stale connections
                for client_id in stale_clients:
                    logger.info(f"Cleaning up stale connection: {client_id}")
                    await self.disconnect(client_id)

                self.stats["last_cleanup"] = current_time
                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(self.cleanup_interval)

    async def _broadcast_data_type(self, data_type: str, monitoring_service):
        """Enhanced broadcast method for specific data types"""
        try:
            if data_type == "status":
                data = await monitoring_service.get_system_status()
                await self.broadcast_to_subscribers("status", data)

            elif data_type == "tasks":
                data = await monitoring_service.get_all_tasks()
                # Limit the number of tasks sent to prevent large payloads
                await self.broadcast_to_subscribers("tasks", data[:50])

            elif data_type == "performance":
                data = await monitoring_service.get_performance_metrics()
                await self.broadcast_to_subscribers("performance", data)

            elif data_type == "analytics":
                data = await monitoring_service.get_task_analytics()
                await self.broadcast_to_subscribers("analytics", data)

            elif data_type == "quality":
                data = await monitoring_service.get_quality_report()
                await self.broadcast_to_subscribers("quality", data)

            elif data_type == "logs":
                # Broadcast recent log activity - implemented as lightweight summary
                # This prevents overwhelming clients with too much log data
                try:
                    # Get recent tasks with logs
                    recent_tasks = await monitoring_service.get_all_tasks()
                    log_summary = {
                        "recent_task_count": len(
                            [
                                t
                                for t in recent_tasks[:10]
                                if t.get("status") == "running"
                            ]
                        ),
                        "error_count": len(
                            [
                                t
                                for t in recent_tasks[:20]
                                if t.get("status") == "failed"
                            ]
                        ),
                        "last_activity": max(
                            [t.get("start_time", 0) for t in recent_tasks[:5]] + [0]
                        )
                        if recent_tasks
                        else 0,
                    }
                    await self.broadcast_to_subscribers("logs", log_summary)
                except Exception:
                    pass  # Skip log broadcasting if there's an issue

        except Exception as e:
            logger.error(f"Error broadcasting {data_type}: {e}")
            self.stats["errors"] += 1

    async def stop_broadcast(self):
        """Enhanced stop broadcast with graceful cleanup"""
        self.is_broadcasting = False
        logger.info("Stopping WebSocket broadcast loop...")

        # Send disconnect notification to all clients
        disconnect_message = {
            "type": "server_shutdown",
            "message": "Server is shutting down",
            "timestamp": time.time(),
        }

        for client_id, connection in list(self.connections.items()):
            try:
                await connection.websocket.send_json(disconnect_message)
                await connection.websocket.close()
            except Exception as e:
                logger.warning(f"Error during graceful disconnect of {client_id}: {e}")

        self.connections.clear()
        logger.info("WebSocket broadcast loop stopped")

    async def _send_initial_data(self, connection: WebSocketConnection):
        """Send enhanced initial data to newly connected client"""
        try:
            from monitoring_service import MonitoringService

            monitoring_service = MonitoringService()

            # Send connection confirmation
            await connection.websocket.send_json(
                {
                    "type": "connection_established",
                    "client_id": connection.client_id,
                    "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "subscriptions": list(connection.subscriptions),
                    "update_frequencies": self.update_frequencies,
                }
            )

            # Send current status
            status = await monitoring_service.get_system_status()
            await connection.websocket.send_json(
                {
                    "type": "initial_data",
                    "data_type": "status",
                    "data": status,
                    "timestamp": time.time(),
                }
            )

            # Send current tasks (limited)
            tasks = await monitoring_service.get_all_tasks()
            await connection.websocket.send_json(
                {
                    "type": "initial_data",
                    "data_type": "tasks",
                    "data": tasks[:20],  # Limit initial load
                    "timestamp": time.time(),
                }
            )

            # Send performance metrics
            performance = await monitoring_service.get_performance_metrics()
            await connection.websocket.send_json(
                {
                    "type": "initial_data",
                    "data_type": "performance",
                    "data": performance,
                    "timestamp": time.time(),
                }
            )

        except Exception as e:
            logger.error(f"Error sending initial data to {connection.client_id}: {e}")
            self.stats["errors"] += 1

    async def broadcast_task_update(self, task_id: str, task_data: Dict):
        """Broadcast a specific task update with enhanced data"""
        await self.broadcast_to_subscribers(
            "task_update",
            {"task_id": task_id, "task_data": task_data, "update_type": "task_update"},
        )

    async def broadcast_system_event(self, event_type: str, event_data: Dict):
        """Broadcast system-level events (phase changes, errors, etc.)"""
        await self.broadcast_to_subscribers(
            "system_event",
            {
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": time.time(),
                "severity": event_data.get("severity", "info"),
            },
        )

    async def handle_client_message(self, websocket: WebSocket, message: Dict):
        """Handle various types of client messages"""
        try:
            message_type = message.get("type")
            client_id = message.get("client_id")

            if message_type == "ping":
                # Handle ping/pong for keepalive
                await websocket.send_json(
                    {"type": "pong", "timestamp": time.time(), "client_id": client_id}
                )

                # Update ping time for connection
                if client_id and client_id in self.connections:
                    self.connections[client_id].update_ping()

            elif message_type == "subscribe":
                await self.handle_subscription(websocket, message)

            elif message_type == "get_stats":
                stats = self.get_connection_stats()
                await websocket.send_json(
                    {"type": "stats_response", "data": stats, "client_id": client_id}
                )

            elif message_type == "request_data":
                # Client requesting immediate data update
                data_type = message.get("data_type", "status")
                await self._handle_data_request(websocket, data_type, client_id)

        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            self.stats["errors"] += 1

    async def _handle_data_request(
        self, websocket: WebSocket, data_type: str, client_id: str
    ):
        """Handle immediate data requests from clients"""
        try:
            from monitoring_service import MonitoringService

            monitoring_service = MonitoringService()

            if data_type == "status":
                data = await monitoring_service.get_system_status()
            elif data_type == "tasks":
                data = await monitoring_service.get_all_tasks()
                data = data[:50]  # Limit data
            elif data_type == "performance":
                data = await monitoring_service.get_performance_metrics()
            elif data_type == "analytics":
                data = await monitoring_service.get_task_analytics()
            elif data_type == "quality":
                data = await monitoring_service.get_quality_report()
            else:
                data = {"error": f"Unknown data type: {data_type}"}

            await websocket.send_json(
                {
                    "type": "data_response",
                    "data_type": data_type,
                    "data": data,
                    "timestamp": time.time(),
                    "client_id": client_id,
                }
            )

        except Exception as e:
            logger.error(f"Error handling data request for {data_type}: {e}")
            self.stats["errors"] += 1

    def get_connection_stats(self) -> Dict:
        """Get enhanced connection statistics"""
        active_subscriptions = {}
        subscription_counts = {}

        for client_id, connection in self.connections.items():
            active_subscriptions[client_id] = {
                "subscriptions": list(connection.subscriptions),
                "connected_at": connection.connected_at,
                "last_ping": connection.last_ping,
                "remote_addr": connection.remote_addr,
                "is_alive": connection.is_alive,
            }

            # Count subscription types
            for sub in connection.subscriptions:
                subscription_counts[sub] = subscription_counts.get(sub, 0) + 1

        return {
            "total_connections": len(self.connections),
            "active_connections": active_subscriptions,
            "subscription_counts": subscription_counts,
            "is_broadcasting": self.is_broadcasting,
            "stats": {
                **self.stats,
                "start_time": self.stats.get("start_time", time.time()),
            },
            "update_frequencies": self.update_frequencies,
        }

    def initialize_stats(self):
        """Initialize statistics tracking"""
        self.stats["start_time"] = time.time()
