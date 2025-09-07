"""
Admin Interface for Message Bus Management.

Provides comprehensive administration capabilities including:
- System monitoring and metrics
- Agent management and control
- Message queue management
- Performance analytics and reporting
- Configuration management
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

try:
    from aiohttp import web
    from aiohttp.web import Application, Request, Response, json_response
except ImportError:
    web = None
    logging.warning("aiohttp package not available - install with: pip install aiohttp")

from ..core.message_bus import MessageBus
from ..core.message_types import Message, MessagePriority, MessageType
from ..gateway.websocket_gateway import WebSocketGateway
from ..routing.message_router import MessageRouter

logger = logging.getLogger(__name__)


class MessageBusAdmin:
    """Administrative interface for message bus management"""

    def __init__(
        self,
        message_bus: MessageBus,
        message_router: Optional[MessageRouter] = None,
        websocket_gateway: Optional[WebSocketGateway] = None,
        host: str = "localhost",
        port: int = 8768,
    ):
        if web is None:
            raise ImportError(
                "aiohttp package required - install with: pip install aiohttp"
            )

        self.message_bus = message_bus
        self.message_router = message_router
        self.websocket_gateway = websocket_gateway
        self.host = host
        self.port = port

        # Web application
        self.app = web.Application()
        self._setup_routes()

        # Admin state
        self.running = False
        self.runner = None
        self.site = None

        # Cached metrics for performance
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0
        self._cache_ttl = 30  # seconds

        logger.info("MessageBusAdmin initialized on %s:%d", host, port)

    def _setup_routes(self) -> None:
        """Setup HTTP routes for admin interface"""
        # Health and status endpoints
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/status", self._handle_status)
        self.app.router.add_get("/metrics", self._handle_metrics)

        # Agent management
        self.app.router.add_get("/agents", self._handle_get_agents)
        self.app.router.add_get("/agents/{agent_id}", self._handle_get_agent)
        self.app.router.add_post("/agents/{agent_id}/kick", self._handle_kick_agent)
        self.app.router.add_post(
            "/agents/{agent_id}/message", self._handle_send_to_agent
        )

        # Group management
        self.app.router.add_get("/groups", self._handle_get_groups)
        self.app.router.add_post(
            "/groups/{group_id}/broadcast", self._handle_group_broadcast
        )

        # Topic management
        self.app.router.add_get("/topics", self._handle_get_topics)
        self.app.router.add_post(
            "/topics/{topic}/broadcast", self._handle_topic_broadcast
        )

        # Message management
        self.app.router.add_get("/messages/stats", self._handle_message_stats)
        self.app.router.add_get("/messages/recent", self._handle_recent_messages)
        self.app.router.add_post("/messages/broadcast", self._handle_system_broadcast)

        # Performance and analytics
        self.app.router.add_get(
            "/analytics/throughput", self._handle_throughput_analytics
        )
        self.app.router.add_get("/analytics/latency", self._handle_latency_analytics)
        self.app.router.add_get("/analytics/errors", self._handle_error_analytics)

        # Configuration management
        self.app.router.add_get("/config", self._handle_get_config)
        self.app.router.add_post("/config", self._handle_update_config)

        # System control
        self.app.router.add_post("/system/gc", self._handle_garbage_collect)
        self.app.router.add_post("/system/shutdown", self._handle_shutdown)

        # Static files for admin dashboard (if available)
        # self.app.router.add_static("/", path="admin_dashboard/", name="admin_dashboard")

    async def start(self) -> None:
        """Start the admin interface"""
        if self.running:
            logger.warning("MessageBusAdmin already running")
            return

        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            self.running = True
            logger.info("MessageBusAdmin started on http://%s:%d", self.host, self.port)

        except Exception as e:
            logger.error("Failed to start MessageBusAdmin: %s", e)
            raise

    async def stop(self) -> None:
        """Stop the admin interface"""
        if not self.running:
            return

        logger.info("Stopping MessageBusAdmin...")
        self.running = False

        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

        logger.info("MessageBusAdmin stopped")

    async def _get_cached_metrics(self) -> Dict[str, Any]:
        """Get cached metrics with TTL"""
        current_time = time.time()

        if current_time - self._cache_timestamp > self._cache_ttl:
            # Refresh cache
            self._metrics_cache = await self._collect_metrics()
            self._cache_timestamp = current_time

        return self._metrics_cache

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        metrics = {
            "timestamp": time.time(),
            "message_bus": {},
            "router": {},
            "gateway": {},
            "system": {},
        }

        # Message bus metrics
        if self.message_bus:
            try:
                bus_stats = await self.message_bus.get_stats()
                bus_health = await self.message_bus.health_check()

                metrics["message_bus"] = {
                    "stats": bus_stats.to_dict(),
                    "health": bus_health,
                    "active_agents": await self.message_bus.get_active_agents(),
                    "groups": await self.message_bus.get_groups(),
                    "topics": await self.message_bus.get_topics(),
                }
            except Exception as e:
                logger.error("Error collecting message bus metrics: %s", e)
                metrics["message_bus"]["error"] = str(e)

        # Router metrics
        if self.message_router:
            try:
                metrics["router"] = self.message_router.get_routing_stats()
            except Exception as e:
                logger.error("Error collecting router metrics: %s", e)
                metrics["router"]["error"] = str(e)

        # Gateway metrics
        if self.websocket_gateway:
            try:
                metrics["gateway"] = self.websocket_gateway.get_connection_stats()
            except Exception as e:
                logger.error("Error collecting gateway metrics: %s", e)
                metrics["gateway"]["error"] = str(e)

        # System metrics
        try:
            import psutil

            metrics["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            }
        except ImportError:
            metrics["system"] = {"note": "psutil not available for system metrics"}
        except Exception as e:
            logger.error("Error collecting system metrics: %s", e)
            metrics["system"]["error"] = str(e)

        return metrics

    # HTTP Handlers

    async def _handle_health(self, request: Request) -> Response:
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {},
            }

            # Check message bus health
            if self.message_bus:
                bus_health = await self.message_bus.health_check()
                health_data["components"]["message_bus"] = bus_health["status"]

            # Check router health (router doesn't have health check, assume healthy if initialized)
            if self.message_router:
                health_data["components"]["router"] = "healthy"

            # Check gateway health
            if self.websocket_gateway:
                health_data["components"]["gateway"] = (
                    "healthy" if self.websocket_gateway.running else "unhealthy"
                )

            # Overall health
            component_statuses = list(health_data["components"].values())
            if all(status == "healthy" for status in component_statuses):
                health_data["status"] = "healthy"
            elif any(status == "healthy" for status in component_statuses):
                health_data["status"] = "degraded"
            else:
                health_data["status"] = "unhealthy"

            return json_response(health_data)

        except Exception as e:
            logger.error("Error in health check: %s", e)
            return json_response(
                {"status": "error", "error": str(e), "timestamp": time.time()},
                status=500,
            )

    async def _handle_status(self, request: Request) -> Response:
        """System status endpoint"""
        try:
            metrics = await self._get_cached_metrics()

            status_data = {
                "running": self.running,
                "uptime": time.time() - self._cache_timestamp,
                "metrics": metrics,
                "admin_info": {
                    "host": self.host,
                    "port": self.port,
                    "cache_ttl": self._cache_ttl,
                },
            }

            return json_response(status_data)

        except Exception as e:
            logger.error("Error getting status: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_metrics(self, request: Request) -> Response:
        """Detailed metrics endpoint"""
        try:
            metrics = await self._collect_metrics()  # Always get fresh metrics
            return json_response(metrics)

        except Exception as e:
            logger.error("Error getting metrics: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_get_agents(self, request: Request) -> Response:
        """Get all agents"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            active_agents = await self.message_bus.get_active_agents()
            agent_details = {}

            for agent_id in active_agents:
                agent_details[agent_id] = {
                    "agent_id": agent_id,
                    "last_seen": self.message_bus.agent_connections.get(agent_id, 0),
                    "connected": agent_id in self.message_bus.agent_connections,
                }

                # Add router info if available
                if self.message_router and agent_id in self.message_router.agents:
                    router_info = self.message_router.agents[agent_id]
                    agent_details[agent_id].update(
                        {
                            "capabilities": list(router_info.capabilities),
                            "load_percentage": router_info.load_percentage,
                            "success_rate": router_info.success_rate,
                            "is_healthy": router_info.is_healthy(),
                        }
                    )

                # Add gateway info if available
                if (
                    self.websocket_gateway
                    and agent_id in self.websocket_gateway.connection_metadata
                ):
                    gateway_info = self.websocket_gateway.connection_metadata[agent_id]
                    agent_details[agent_id].update(
                        {
                            "websocket_connected": True,
                            "connected_at": gateway_info.get("connected_at"),
                            "client_capabilities": gateway_info.get("capabilities", []),
                        }
                    )

            return json_response(
                {"total_agents": len(active_agents), "agents": agent_details}
            )

        except Exception as e:
            logger.error("Error getting agents: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_get_agent(self, request: Request) -> Response:
        """Get specific agent details"""
        try:
            agent_id = request.match_info["agent_id"]

            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            if agent_id not in self.message_bus.agent_connections:
                return json_response({"error": "Agent not found"}, status=404)

            agent_data = {
                "agent_id": agent_id,
                "last_seen": self.message_bus.agent_connections[agent_id],
                "connected": True,
            }

            # Add router information
            if self.message_router and agent_id in self.message_router.agents:
                router_info = self.message_router.agents[agent_id]
                agent_data.update(
                    {
                        "capabilities": list(router_info.capabilities),
                        "current_load": router_info.current_load,
                        "max_load": router_info.max_load,
                        "load_percentage": router_info.load_percentage,
                        "success_count": router_info.success_count,
                        "failure_count": router_info.failure_count,
                        "success_rate": router_info.success_rate,
                        "response_time_ms": router_info.response_time_ms,
                        "is_healthy": router_info.is_healthy(),
                        "location": router_info.location,
                    }
                )

                # Circuit breaker info
                if agent_id in self.message_router.circuit_breakers:
                    cb = self.message_router.circuit_breakers[agent_id]
                    agent_data["circuit_breaker"] = {
                        "state": cb.state.value,
                        "failure_count": cb.failure_count,
                        "success_count": cb.success_count,
                        "can_execute": cb.can_execute(),
                    }

            # Add gateway information
            if (
                self.websocket_gateway
                and agent_id in self.websocket_gateway.connection_metadata
            ):
                gateway_info = self.websocket_gateway.connection_metadata[agent_id]
                agent_data.update(
                    {
                        "websocket_connected": True,
                        "connected_at": gateway_info.get("connected_at"),
                        "client_info": gateway_info.get("client_info", {}),
                        "websocket_capabilities": gateway_info.get("capabilities", []),
                    }
                )

            return json_response(agent_data)

        except Exception as e:
            logger.error(
                "Error getting agent %s: %s", request.match_info.get("agent_id"), e
            )
            return json_response({"error": str(e)}, status=500)

    async def _handle_kick_agent(self, request: Request) -> Response:
        """Forcefully disconnect an agent"""
        try:
            agent_id = request.match_info["agent_id"]

            success = False

            # Disconnect from WebSocket gateway
            if (
                self.websocket_gateway
                and agent_id in self.websocket_gateway.connections
            ):
                websocket = self.websocket_gateway.connections[agent_id]
                await self.websocket_gateway._close_connection(
                    websocket, "Kicked by admin"
                )
                success = True

            # Unregister from message bus
            if self.message_bus:
                await self.message_bus.unregister_agent(agent_id)
                success = True

            # Unregister from router
            if self.message_router:
                self.message_router.unregister_agent(agent_id)
                success = True

            return json_response(
                {
                    "success": success,
                    "message": f"Agent {agent_id} has been kicked"
                    if success
                    else "Agent not found or not connected",
                }
            )

        except Exception as e:
            logger.error(
                "Error kicking agent %s: %s", request.match_info.get("agent_id"), e
            )
            return json_response({"error": str(e)}, status=500)

    async def _handle_send_to_agent(self, request: Request) -> Response:
        """Send a message to specific agent"""
        try:
            agent_id = request.match_info["agent_id"]
            data = await request.json()

            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            # Create admin message
            message = Message(
                sender_id="admin",
                recipient_id=agent_id,
                message_type=MessageType.POINT_TO_POINT,
                priority=MessagePriority.HIGH,
                payload=data.get("payload", {}),
                correlation_id=data.get("correlation_id"),
            )

            success = await self.message_bus.send_message(message)

            return json_response(
                {
                    "success": success,
                    "message_id": message.message_id,
                    "recipient": agent_id,
                }
            )

        except Exception as e:
            logger.error("Error sending message to agent: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_get_groups(self, request: Request) -> Response:
        """Get all groups and their members"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            groups = await self.message_bus.get_groups()

            group_details = {}
            for group_id, members in groups.items():
                group_details[group_id] = {
                    "group_id": group_id,
                    "member_count": len(members),
                    "members": members,
                }

            return json_response({"total_groups": len(groups), "groups": group_details})

        except Exception as e:
            logger.error("Error getting groups: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_group_broadcast(self, request: Request) -> Response:
        """Broadcast message to a group"""
        try:
            group_id = request.match_info["group_id"]
            data = await request.json()

            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            message = Message(
                sender_id="admin",
                group_id=group_id,
                message_type=MessageType.GROUP,
                priority=MessagePriority.NORMAL,
                payload=data.get("payload", {}),
            )

            success = await self.message_bus.send_message(message)

            return json_response(
                {
                    "success": success,
                    "message_id": message.message_id,
                    "group_id": group_id,
                }
            )

        except Exception as e:
            logger.error("Error broadcasting to group: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_get_topics(self, request: Request) -> Response:
        """Get all topics and their subscribers"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            topics = await self.message_bus.get_topics()

            topic_details = {}
            for topic, subscribers in topics.items():
                topic_details[topic] = {
                    "topic": topic,
                    "subscriber_count": len(subscribers),
                    "subscribers": subscribers,
                }

            return json_response({"total_topics": len(topics), "topics": topic_details})

        except Exception as e:
            logger.error("Error getting topics: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_topic_broadcast(self, request: Request) -> Response:
        """Broadcast message to a topic"""
        try:
            topic = request.match_info["topic"]
            data = await request.json()

            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            message = Message(
                sender_id="admin",
                topic=topic,
                message_type=MessageType.TOPIC,
                priority=MessagePriority.NORMAL,
                payload=data.get("payload", {}),
            )

            success = await self.message_bus.send_message(message)

            return json_response(
                {"success": success, "message_id": message.message_id, "topic": topic}
            )

        except Exception as e:
            logger.error("Error broadcasting to topic: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_message_stats(self, request: Request) -> Response:
        """Get message statistics"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            stats = await self.message_bus.get_stats()

            return json_response(
                {
                    "message_stats": stats.to_dict(),
                    "additional_metrics": {
                        "messages_per_second": stats.total_sent
                        / max(1, time.time() - self._cache_timestamp),
                        "error_rate": (stats.total_failed / max(1, stats.total_sent))
                        * 100,
                        "success_rate": (
                            (stats.total_sent - stats.total_failed)
                            / max(1, stats.total_sent)
                        )
                        * 100,
                    },
                }
            )

        except Exception as e:
            logger.error("Error getting message stats: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_recent_messages(self, request: Request) -> Response:
        """Get recent messages (limited implementation)"""
        try:
            # This would require more sophisticated message tracking
            # For now, return placeholder
            return json_response(
                {
                    "note": "Recent messages tracking not implemented yet",
                    "suggestion": "Use Redis CLI to inspect message streams directly",
                }
            )

        except Exception as e:
            logger.error("Error getting recent messages: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_system_broadcast(self, request: Request) -> Response:
        """Send system-wide broadcast message"""
        try:
            data = await request.json()

            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            message = Message(
                sender_id="admin",
                message_type=MessageType.SYSTEM,
                priority=MessagePriority.HIGH,
                payload=data.get("payload", {}),
            )

            success = await self.message_bus.send_message(message)

            return json_response(
                {
                    "success": success,
                    "message_id": message.message_id,
                    "broadcast_type": "system",
                }
            )

        except Exception as e:
            logger.error("Error sending system broadcast: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_throughput_analytics(self, request: Request) -> Response:
        """Get throughput analytics"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            stats = await self.message_bus.get_stats()

            # Simple throughput calculation
            throughput_data = {
                "total_messages": stats.total_sent,
                "current_rate_estimate": stats.total_sent
                / max(1, time.time() - self._cache_timestamp),
                "note": "More sophisticated analytics require time-series data collection",
            }

            return json_response(throughput_data)

        except Exception as e:
            logger.error("Error getting throughput analytics: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_latency_analytics(self, request: Request) -> Response:
        """Get latency analytics"""
        try:
            if not self.message_bus:
                return json_response({"error": "Message bus not available"}, status=503)

            stats = await self.message_bus.get_stats()

            latency_data = {
                "average_delivery_time_ms": stats.average_delivery_time_ms,
                "average_processing_time_ms": stats.average_processing_time_ms,
                "note": "More detailed latency analytics require enhanced tracking",
            }

            return json_response(latency_data)

        except Exception as e:
            logger.error("Error getting latency analytics: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_error_analytics(self, request: Request) -> Response:
        """Get error analytics"""
        try:
            analytics_data = {
                "message_bus_errors": 0,
                "router_errors": 0,
                "gateway_errors": 0,
                "note": "Error analytics require enhanced logging and tracking",
            }

            if self.message_bus:
                stats = await self.message_bus.get_stats()
                analytics_data["message_bus_errors"] = stats.total_failed

            if self.message_router:
                router_stats = self.message_router.get_routing_stats()
                analytics_data["router_errors"] = router_stats["routing_stats"][
                    "failed_routes"
                ]

            return json_response(analytics_data)

        except Exception as e:
            logger.error("Error getting error analytics: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_get_config(self, request: Request) -> Response:
        """Get current configuration"""
        try:
            config_data = {
                "message_bus": {
                    "redis_url": self.message_bus.redis_url
                    if self.message_bus
                    else None,
                    "max_connections": self.message_bus.max_connections
                    if self.message_bus
                    else None,
                    "enable_compression": self.message_bus.enable_compression
                    if self.message_bus
                    else None,
                    "default_ttl": self.message_bus.default_ttl
                    if self.message_bus
                    else None,
                },
                "admin": {
                    "host": self.host,
                    "port": self.port,
                    "cache_ttl": self._cache_ttl,
                },
                "gateway": {
                    "host": self.websocket_gateway.host
                    if self.websocket_gateway
                    else None,
                    "port": self.websocket_gateway.port
                    if self.websocket_gateway
                    else None,
                    "max_connections": self.websocket_gateway.max_connections
                    if self.websocket_gateway
                    else None,
                },
            }

            return json_response(config_data)

        except Exception as e:
            logger.error("Error getting config: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_update_config(self, request: Request) -> Response:
        """Update configuration (limited implementation)"""
        try:
            data = await request.json()

            # For now, only allow updating cache TTL
            if "cache_ttl" in data:
                self._cache_ttl = max(
                    10, min(300, int(data["cache_ttl"]))
                )  # 10s to 5min

            return json_response(
                {
                    "success": True,
                    "updated": ["cache_ttl"] if "cache_ttl" in data else [],
                    "note": "Only limited config updates supported",
                }
            )

        except Exception as e:
            logger.error("Error updating config: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_garbage_collect(self, request: Request) -> Response:
        """Force garbage collection"""
        try:
            import gc

            # Force garbage collection
            collected = gc.collect()

            # Clear metrics cache
            self._metrics_cache.clear()
            self._cache_timestamp = 0

            return json_response(
                {"success": True, "garbage_collected": collected, "cache_cleared": True}
            )

        except Exception as e:
            logger.error("Error during garbage collection: %s", e)
            return json_response({"error": str(e)}, status=500)

    async def _handle_shutdown(self, request: Request) -> Response:
        """Shutdown the system gracefully"""
        try:
            # This is a placeholder - in a real system you'd want proper authorization

            return json_response(
                {
                    "success": False,
                    "message": "Shutdown disabled for safety - implement proper authorization first",
                },
                status=403,
            )

        except Exception as e:
            logger.error("Error during shutdown: %s", e)
            return json_response({"error": str(e)}, status=500)

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin interface statistics"""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "cache_ttl": self._cache_ttl,
            "cache_size": len(self._metrics_cache),
            "cache_age": time.time() - self._cache_timestamp,
            "components": {
                "message_bus": self.message_bus is not None,
                "message_router": self.message_router is not None,
                "websocket_gateway": self.websocket_gateway is not None,
            },
        }
