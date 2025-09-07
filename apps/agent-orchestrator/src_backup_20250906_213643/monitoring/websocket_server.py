"""
WebSocket Server for Real-time Monitoring
Streams metrics data to dashboard clients in real-time
"""
import asyncio
import json
import logging
import ssl
from typing import Any, Dict, List, Optional, Set

try:
    import websockets
except ImportError:
    websockets = None
    logging.warning(
        "websockets package not available - install with: pip install websockets"
    )

from .metrics_collector import Metric, MetricsCollector, get_global_collector

logger = logging.getLogger(__name__)


class MonitoringWebSocketServer:
    """WebSocket server for streaming metrics data"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        collector: Optional[MetricsCollector] = None,
    ):
        if websockets is None:
            raise ImportError(
                "websockets package required - install with: pip install websockets"
            )

        self.host = host
        self.port = port
        self.collector = collector or get_global_collector()

        # Client management
        self.clients: Set[Any] = set()  # websockets.WebSocketServerProtocol
        self.client_subscriptions: Dict[Any, Set[str]] = {}  # client -> {metric_types}

        # Server state
        self.server = None
        self.running = False

        # Subscribe to metrics collector
        self.collector.subscribe(self._on_metric_received)

        logger.info("MonitoringWebSocketServer initialized on %s:%d", host, port)

    async def start_server(self, ssl_context: Optional[ssl.SSLContext] = None) -> None:
        """Start the WebSocket server"""
        if websockets is None:
            raise ImportError("websockets package required")

        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10,
                max_size=10**6,  # 1MB max message size
                max_queue=100,  # Max queued messages per client
            )
            self.running = True
            logger.info("WebSocket server started on %s:%d", self.host, self.port)

            # Send initial data to any connected clients
            await self._broadcast_initial_data()

        except Exception as e:
            logger.error("Failed to start WebSocket server: %s", e)
            raise

    async def stop_server(self) -> None:
        """Stop the WebSocket server"""
        if self.server:
            self.running = False

            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[client.close() for client in self.clients], return_exceptions=True
                )

            # Stop the server
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    async def _handle_client(self, websocket: Any, path: str) -> None:
        """Handle individual client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info("Client connected: %s", client_id)

        # Add client
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()

        try:
            # Send welcome message and initial data
            await self._send_welcome(websocket)
            await self._send_initial_data(websocket)

            # Handle client messages
            async for message in websocket:
                try:
                    await self._process_client_message(websocket, message)
                except Exception as e:
                    logger.error("Error processing client message: %s", e)
                    await self._send_error(websocket, str(e))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected: %s", client_id)
        except Exception as e:
            logger.error("Error handling client %s: %s", client_id, e)
        finally:
            # Cleanup
            self.clients.discard(websocket)
            self.client_subscriptions.pop(websocket, None)

    async def _process_client_message(self, websocket: Any, message: str) -> None:
        """Process incoming client messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe":
                # Subscribe to specific metric types
                metric_types = data.get("metric_types", [])
                self.client_subscriptions[websocket] = set(metric_types)
                await self._send_response(
                    websocket,
                    "subscription_updated",
                    {"subscribed_types": list(self.client_subscriptions[websocket])},
                )

            elif message_type == "get_summary":
                # Send current metrics summary
                summary = self.collector.get_summary()
                await self._send_response(websocket, "summary", summary.__dict__)

            elif message_type == "get_recent_metrics":
                # Send recent metrics
                seconds = data.get("seconds", 300)
                metrics = self.collector.get_recent_metrics(seconds)
                await self._send_response(
                    websocket,
                    "recent_metrics",
                    {"metrics": metrics, "time_window_seconds": seconds},
                )

            elif message_type == "get_active_tasks":
                # Send active tasks
                active_tasks = self.collector.get_active_tasks()
                await self._send_response(
                    websocket, "active_tasks", {"tasks": active_tasks}
                )

            elif message_type == "ping":
                # Respond to ping
                await self._send_response(
                    websocket, "pong", {"timestamp": data.get("timestamp")}
                )

            else:
                await self._send_error(
                    websocket, f"Unknown message type: {message_type}"
                )

        except json.JSONDecodeError as e:
            await self._send_error(websocket, f"Invalid JSON: {e}")
        except Exception as e:
            await self._send_error(websocket, f"Error processing message: {e}")

    async def _send_welcome(self, websocket: Any) -> None:
        """Send welcome message to new client"""
        welcome_data = {
            "type": "welcome",
            "server": "Agent Orchestrator Monitoring Server",
            "version": "1.0.0",
            "available_subscriptions": [
                "task_started",
                "task_completed",
                "task_failed",
                "agent_spawn",
                "agent_terminate",
                "token_usage",
                "execution_time",
                "memory_usage",
                "error_rate",
                "throughput",
                "queue_depth",
                "resource_utilization",
            ],
        }
        await websocket.send(json.dumps(welcome_data))

    async def _send_initial_data(self, websocket: Any) -> None:
        """Send initial data to client"""
        # Send current summary
        summary = self.collector.get_summary()
        await self._send_response(websocket, "initial_summary", summary.__dict__)

        # Send recent metrics (last 60 seconds)
        recent_metrics = self.collector.get_recent_metrics(60)
        await self._send_response(
            websocket, "initial_metrics", {"metrics": recent_metrics}
        )

        # Send active tasks
        active_tasks = self.collector.get_active_tasks()
        await self._send_response(websocket, "active_tasks", {"tasks": active_tasks})

    async def _send_response(
        self, websocket: Any, response_type: str, data: Dict[str, Any]
    ) -> None:
        """Send response to client"""
        response = {
            "type": response_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data,
        }
        try:
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error("Error sending response to client: %s", e)

    async def _send_error(self, websocket: Any, error_message: str) -> None:
        """Send error response to client"""
        error_response = {
            "type": "error",
            "timestamp": asyncio.get_event_loop().time(),
            "error": error_message,
        }
        try:
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error("Error sending error to client: %s", e)

    async def _broadcast_initial_data(self) -> None:
        """Broadcast initial data to all connected clients"""
        if not self.clients:
            return

        # Send initial data to all clients
        await asyncio.gather(
            *[self._send_initial_data(client) for client in self.clients],
            return_exceptions=True,
        )

    def _on_metric_received(self, metric: Metric) -> None:
        """Handle new metric from collector"""
        if not self.running or not self.clients:
            return

        # Create broadcast task
        asyncio.create_task(self._broadcast_metric(metric))

    async def _broadcast_metric(self, metric: Metric) -> None:
        """Broadcast metric to subscribed clients"""
        metric_data = {
            "type": "metric",
            "timestamp": asyncio.get_event_loop().time(),
            "data": metric.to_dict(),
        }
        message = json.dumps(metric_data)

        # Send to subscribed clients
        tasks = []
        for client in list(self.clients):  # Copy to avoid modification during iteration
            client_subscriptions = self.client_subscriptions.get(client, set())

            # Send if client is subscribed to this metric type or subscribed to all
            if (
                not client_subscriptions
                or metric.metric_type.value in client_subscriptions
                or "all" in client_subscriptions
            ):
                tasks.append(self._send_metric_to_client(client, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_metric_to_client(self, client: Any, message: str) -> None:
        """Send metric message to individual client"""
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected, will be cleaned up elsewhere
            pass
        except Exception as e:
            logger.error("Error sending metric to client: %s", e)
            # Remove problematic client
            self.clients.discard(client)
            self.client_subscriptions.pop(client, None)

    def get_connected_clients(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)

    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "host": self.host,
            "port": self.port,
            "running": self.running,
            "connected_clients": len(self.clients),
            "total_subscriptions": sum(
                len(subs) for subs in self.client_subscriptions.values()
            ),
        }
