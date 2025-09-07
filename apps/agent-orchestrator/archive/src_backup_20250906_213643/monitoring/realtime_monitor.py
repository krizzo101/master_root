"""
Real-time Monitor Coordinator
Orchestrates the complete monitoring system with WebSocket streaming and web dashboard
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from .dashboard_server import DashboardServer
from .metrics_collector import Metric, MetricsCollector, get_global_collector
from .websocket_server import MonitoringWebSocketServer

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """Main coordinator for the real-time monitoring system"""

    def __init__(
        self,
        dashboard_host: str = "localhost",
        dashboard_port: int = 8766,
        websocket_host: str = "localhost",
        websocket_port: int = 8765,
        collector: Optional[MetricsCollector] = None,
    ):
        self.collector = collector or get_global_collector()

        # Initialize servers
        self.dashboard_server = DashboardServer(
            host=dashboard_host, port=dashboard_port, collector=self.collector
        )

        self.websocket_server = MonitoringWebSocketServer(
            host=websocket_host, port=websocket_port, collector=self.collector
        )

        self.running = False

        # Subscribe to metrics for dashboard broadcasting
        self.collector.subscribe(self._on_metric_received)

        logger.info("RealtimeMonitor initialized")

    async def start(self) -> None:
        """Start all monitoring services"""
        try:
            logger.info("Starting real-time monitoring system...")

            # Start dashboard server
            await self.dashboard_server.start_server()

            # Start WebSocket server
            await self.websocket_server.start_server()

            self.running = True
            logger.info("Real-time monitoring system started successfully")
            logger.info(
                "Dashboard: http://%s:%d",
                self.dashboard_server.host,
                self.dashboard_server.port,
            )
            logger.info(
                "WebSocket API: ws://%s:%d",
                self.websocket_server.host,
                self.websocket_server.port,
            )

        except Exception as e:
            logger.error("Failed to start monitoring system: %s", e)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop all monitoring services"""
        if not self.running:
            return

        logger.info("Stopping real-time monitoring system...")
        self.running = False

        try:
            # Stop WebSocket server
            await self.websocket_server.stop_server()

            # Dashboard server stops automatically with the event loop

            # Unsubscribe from metrics
            self.collector.unsubscribe(self._on_metric_received)

            logger.info("Real-time monitoring system stopped")
        except Exception as e:
            logger.error("Error stopping monitoring system: %s", e)

    def _on_metric_received(self, metric: Metric) -> None:
        """Handle new metrics by broadcasting to dashboard WebSocket clients"""
        if not self.running:
            return

        # Create broadcast task for dashboard
        asyncio.create_task(self._broadcast_metric_to_dashboard(metric))

    async def _broadcast_metric_to_dashboard(self, metric: Metric) -> None:
        """Broadcast metric to dashboard WebSocket connections"""
        try:
            message = {"type": "metric", "data": metric.to_dict()}
            await self.dashboard_server.broadcast_to_websockets(message)
        except Exception as e:
            logger.error("Error broadcasting metric to dashboard: %s", e)

    def get_status(self) -> dict:
        """Get status of all monitoring components"""
        return {
            "running": self.running,
            "dashboard_server": {
                "host": self.dashboard_server.host,
                "port": self.dashboard_server.port,
                "websocket_connections": len(
                    self.dashboard_server.websocket_connections
                ),
            },
            "websocket_server": self.websocket_server.get_server_stats(),
            "metrics_collector": {
                "active_tasks": len(self.collector.get_active_tasks()),
                "active_agents": len(self.collector.get_active_agents()),
                "summary": self.collector.get_summary().__dict__,
            },
        }

    async def run_forever(self) -> None:
        """Run the monitoring system indefinitely"""
        await self.start()

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received signal %d, shutting down...", signum)
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            await self.stop()


async def main():
    """Main entry point for running the monitoring system"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    monitor = RealtimeMonitor()

    try:
        await monitor.run_forever()
    except Exception as e:
        logger.error("Error running monitor: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
