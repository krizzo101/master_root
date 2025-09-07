#!/usr/bin/env python3
"""
Production Message Bus Server for Agent Collaboration

High-performance Redis-based pub/sub messaging system that handles 50+ concurrent
agents efficiently with real-time WebSocket connections, message routing, and
delivery confirmation.

Features:
- Redis Streams + Pub/Sub for scalable messaging
- WebSocket gateway for real-time connections
- Topic-based message routing with load balancing
- Performance monitoring and admin interface
- Message persistence and replay capabilities
- Connection management and heartbeat monitoring

Usage:
    python message_bus_server.py [--redis-url REDIS_URL] [--websocket-port PORT] [--admin-port PORT]
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from src.message_bus.admin.admin_interface import MessageBusAdmin
from src.message_bus.core.message_bus import MessageBus
from src.message_bus.gateway.websocket_gateway import WebSocketGateway
from src.message_bus.routing.message_router import MessageRouter

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("message_bus.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


class MessageBusServer:
    """Production-ready message bus server orchestrator"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        websocket_port: int = 8767,
        admin_port: int = 8768,
        max_connections: int = 1000,
    ):
        self.redis_url = redis_url
        self.websocket_port = websocket_port
        self.admin_port = admin_port
        self.max_connections = max_connections

        # Core components
        self.message_bus: Optional[MessageBus] = None
        self.websocket_gateway: Optional[WebSocketGateway] = None
        self.message_router: Optional[MessageRouter] = None
        self.admin_interface: Optional[MessageBusAdmin] = None

        # Server state
        self.running = False
        self.shutdown_event = asyncio.Event()

        logger.info("MessageBusServer initialized")

    async def start(self) -> None:
        """Start all message bus components"""
        if self.running:
            logger.warning("MessageBusServer already running")
            return

        try:
            logger.info("Starting MessageBusServer...")

            # 1. Initialize core message bus with Redis
            logger.info("Starting message bus with Redis: %s", self.redis_url)
            self.message_bus = MessageBus(
                redis_url=self.redis_url,
                max_connections=self.max_connections,
                enable_compression=True,
                compression_threshold=1024,
                default_ttl=3600,
                enable_persistence=True,
            )
            await self.message_bus.start()

            # 2. Initialize message router for load balancing
            logger.info("Starting message router...")
            self.message_router = MessageRouter(message_bus=self.message_bus)
            await self.message_router.start()

            # 3. Initialize WebSocket gateway for real-time connections
            logger.info("Starting WebSocket gateway on port %d", self.websocket_port)
            self.websocket_gateway = WebSocketGateway(
                message_bus=self.message_bus,
                port=self.websocket_port,
                max_connections=self.max_connections,
            )
            await self.websocket_gateway.start()

            # 4. Initialize admin interface
            logger.info("Starting admin interface on port %d", self.admin_port)
            self.admin_interface = MessageBusAdmin(
                message_bus=self.message_bus,
                message_router=self.message_router,
                websocket_gateway=self.websocket_gateway,
                port=self.admin_port,
            )
            await self.admin_interface.start()

            self.running = True
            logger.info("MessageBusServer started successfully!")

            # Print startup summary
            print("\n" + "=" * 60)
            print("🚀 MESSAGE BUS SERVER STARTED")
            print("=" * 60)
            print(f"📡 WebSocket Gateway: ws://localhost:{self.websocket_port}")
            print(f"🔧 Admin Interface: http://localhost:{self.admin_port}")
            print(f"🗄️  Redis Backend: {self.redis_url}")
            print(f"⚡ Max Connections: {self.max_connections}")
            print("=" * 60)
            print("\nReady to handle agent connections!")
            print("Press Ctrl+C to stop the server\n")

        except Exception as e:
            logger.error("Failed to start MessageBusServer: %s", e)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop all message bus components gracefully"""
        if not self.running:
            logger.info("MessageBusServer already stopped")
            return

        logger.info("Stopping MessageBusServer...")

        # Stop components in reverse order
        try:
            if self.admin_interface:
                await self.admin_interface.stop()
                logger.info("Admin interface stopped")

            if self.websocket_gateway:
                await self.websocket_gateway.stop()
                logger.info("WebSocket gateway stopped")

            if self.message_router:
                await self.message_router.stop()
                logger.info("Message router stopped")

            if self.message_bus:
                await self.message_bus.stop()
                logger.info("Message bus stopped")

        except Exception as e:
            logger.error("Error during shutdown: %s", e)

        self.running = False
        self.shutdown_event.set()
        logger.info("MessageBusServer stopped")

    async def run_forever(self) -> None:
        """Run server until shutdown signal received"""
        await self.shutdown_event.wait()

    def get_status(self) -> dict:
        """Get comprehensive server status"""
        status = {
            "running": self.running,
            "redis_url": self.redis_url,
            "websocket_port": self.websocket_port,
            "admin_port": self.admin_port,
            "max_connections": self.max_connections,
            "components": {
                "message_bus": bool(self.message_bus),
                "websocket_gateway": bool(self.websocket_gateway),
                "message_router": bool(self.message_router),
                "admin_interface": bool(self.admin_interface),
            },
        }

        # Add component-specific status if available
        if self.message_bus:
            status["message_bus_stats"] = self.message_bus.get_stats()

        if self.websocket_gateway:
            status["websocket_connections"] = len(self.websocket_gateway.connections)

        return status


async def main():
    """Main server entry point"""
    parser = argparse.ArgumentParser(
        description="Agent Collaboration Message Bus Server"
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis connection URL (default: redis://localhost:6379/0)",
    )
    parser.add_argument(
        "--websocket-port",
        type=int,
        default=8767,
        help="WebSocket server port (default: 8767)",
    )
    parser.add_argument(
        "--admin-port",
        type=int,
        default=8768,
        help="Admin interface port (default: 8768)",
    )
    parser.add_argument(
        "--max-connections",
        type=int,
        default=1000,
        help="Maximum concurrent connections (default: 1000)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create and start server
    server = MessageBusServer(
        redis_url=args.redis_url,
        websocket_port=args.websocket_port,
        admin_port=args.admin_port,
        max_connections=args.max_connections,
    )

    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Received signal %d, initiating shutdown...", sig)
        asyncio.create_task(server.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start()
        await server.run_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Server error: %s", e)
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Message Bus Server shutdown complete!")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)
