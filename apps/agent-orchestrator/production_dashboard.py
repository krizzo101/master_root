#!/usr/bin/env python3
"""
Production Dashboard Server
Enterprise-ready deployment with auto-restart, logging, and monitoring
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import aiohttp
from aiohttp import web

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from monitoring.dashboard_server import DashboardServer
from monitoring.metrics_collector import get_global_collector


class ProductionDashboardManager:
    """Production-ready dashboard server manager"""

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.server: Optional[DashboardServer] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.shutdown_event = asyncio.Event()

        # Setup production logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # Health check server
        self.health_server: Optional[web.Application] = None
        self.health_runner: Optional[web.AppRunner] = None
        self.health_site: Optional[web.TCPSite] = None

    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """Load production configuration"""
        default_config = {
            "host": "0.0.0.0",
            "port": 8765,
            "health_port": 8766,
            "max_connections": 100,
            "keepalive_timeout": 30,
            "client_timeout": 60,
            "graceful_shutdown_timeout": 30,
            "static_dir": None,
            "log_level": "INFO",
            "log_file": "logs/dashboard_production.log",
            "max_log_size": 50 * 1024 * 1024,  # 50MB
            "backup_count": 5,
            "metrics_retention_seconds": 3600,
            "websocket_ping_interval": 30,
            "websocket_timeout": 60,
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                print(f"✅ Loaded configuration from {config_file}")
            except Exception as e:
                print(f"⚠️ Failed to load config {config_file}: {e}")
                print("📋 Using default configuration")

        # Environment variable overrides
        env_overrides = {
            "DASHBOARD_HOST": "host",
            "DASHBOARD_PORT": "port",
            "DASHBOARD_LOG_LEVEL": "log_level",
            "DASHBOARD_MAX_CONNECTIONS": "max_connections",
        }

        for env_var, config_key in env_overrides.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                if config_key in ["port", "health_port", "max_connections"]:
                    value = int(value)
                default_config[config_key] = value
                print(f"📝 Override from {env_var}: {config_key}={value}")

        return default_config

    def _setup_logging(self):
        """Setup production logging with rotation"""
        log_dir = Path(self.config["log_file"]).parent
        log_dir.mkdir(exist_ok=True, parents=True)

        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config["log_level"]))

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # File handler with rotation
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            self.config["log_file"],
            maxBytes=self.config["max_log_size"],
            backupCount=self.config["backup_count"],
        )

        # Console handler
        console_handler = logging.StreamHandler()

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        print(f"📁 Logging to: {self.config['log_file']}")
        print(f"📊 Log level: {self.config['log_level']}")

    async def _setup_health_check_server(self):
        """Setup health check endpoint on separate port"""
        self.health_server = web.Application()

        async def health_check(request):
            """Health check endpoint"""
            status = {
                "status": "healthy",
                "timestamp": time.time(),
                "uptime": time.time() - self.start_time,
                "dashboard_running": self.server is not None,
                "websocket_connections": len(self.server.websocket_connections)
                if self.server
                else 0,
                "collector_active": get_global_collector() is not None,
            }

            # Check if main dashboard is responsive
            try:
                timeout = aiohttp.ClientTimeout(total=2.0)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"http://{self.config['host']}:{self.config['port']}/api/summary"
                    async with session.get(url) as resp:
                        status["dashboard_responsive"] = resp.status == 200
            except:
                status["dashboard_responsive"] = False
                status["status"] = "degraded"

            return web.json_response(status)

        async def ready_check(request):
            """Readiness check - only ready when dashboard is fully operational"""
            if (
                self.server
                and self.site
                and hasattr(self.site, "_server")
                and self.site._server
            ):
                return web.json_response({"status": "ready"})
            else:
                return web.json_response({"status": "not_ready"}, status=503)

        self.health_server.router.add_get("/health", health_check)
        self.health_server.router.add_get("/ready", ready_check)

        self.health_runner = web.AppRunner(self.health_server)
        await self.health_runner.setup()

        self.health_site = web.TCPSite(
            self.health_runner, self.config["host"], self.config["health_port"]
        )
        await self.health_site.start()

        self.logger.info(
            f"🩺 Health check server started on {self.config['host']}:{self.config['health_port']}"
        )

    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""

        def signal_handler(signum, frame):
            self.logger.info(f"📡 Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # On Unix systems, also handle SIGUSR1 for graceful restart
        if hasattr(signal, "SIGUSR1"):
            signal.signal(signal.SIGUSR1, signal_handler)

    async def start(self) -> bool:
        """Start the production dashboard server"""
        self.start_time = time.time()

        try:
            self.logger.info("🚀 Starting production dashboard server...")

            # Setup signal handlers
            self._setup_signal_handlers()

            # Create dashboard server with production config
            self.server = DashboardServer(
                host=self.config["host"],
                port=self.config["port"],
                static_dir=self.config["static_dir"],
            )

            # Configure production settings
            self.server.app._client_timeout = self.config["client_timeout"]

            # Start health check server first
            await self._setup_health_check_server()

            # Start main dashboard server
            self.runner = web.AppRunner(
                self.server.app, keepalive_timeout=self.config["keepalive_timeout"]
            )
            await self.runner.setup()

            self.site = web.TCPSite(
                self.runner, self.config["host"], self.config["port"]
            )
            await self.site.start()

            self.logger.info(
                f"✅ Dashboard server started on http://{self.config['host']}:{self.config['port']}"
            )
            self.logger.info(f"📊 Max connections: {self.config['max_connections']}")
            self.logger.info(
                f"⏱️  Keepalive timeout: {self.config['keepalive_timeout']}s"
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start dashboard server: {e}")
            await self.cleanup()
            return False

    async def run_until_shutdown(self):
        """Run the server until shutdown signal received"""
        self.logger.info("👂 Waiting for shutdown signal...")

        # Monitor for workflow directories and auto-monitor
        monitor_task = asyncio.create_task(self._monitor_workflows())

        try:
            await self.shutdown_event.wait()
        except Exception as e:
            self.logger.error(f"Error during runtime: {e}")
        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_workflows(self):
        """Monitor for new workflow directories and automatically track them"""
        outputs_dir = Path("outputs")
        known_workflows = set()

        while not self.shutdown_event.is_set():
            try:
                if outputs_dir.exists():
                    for workflow_dir in outputs_dir.iterdir():
                        if (
                            workflow_dir.is_dir()
                            and workflow_dir.name not in known_workflows
                        ):
                            self.logger.info(
                                f"📁 Detected new workflow: {workflow_dir.name}"
                            )
                            known_workflows.add(workflow_dir.name)

                            # TODO: Integrate with workflow monitoring
                            # This is where you'd connect to the GenericOrchestrator
                            # dashboard callback system

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring workflows: {e}")
                await asyncio.sleep(30)

    async def shutdown(self):
        """Graceful shutdown with timeout"""
        self.logger.info("🛑 Initiating graceful shutdown...")

        try:
            # Stop accepting new connections
            if self.site:
                await self.site.stop()
                self.logger.info("🔌 Stopped accepting new connections")

            if self.health_site:
                await self.health_site.stop()

            # Close existing WebSocket connections
            if self.server and self.server.websocket_connections:
                self.logger.info(
                    f"🌐 Closing {len(self.server.websocket_connections)} WebSocket connections..."
                )

                close_tasks = []
                for ws in list(self.server.websocket_connections):
                    if not ws.closed:
                        close_tasks.append(ws.close())

                if close_tasks:
                    await asyncio.gather(*close_tasks, return_exceptions=True)

            # Wait for graceful shutdown timeout
            await asyncio.sleep(min(self.config["graceful_shutdown_timeout"], 5))

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        await self.cleanup()
        self.logger.info("✅ Shutdown complete")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.runner:
                await self.runner.cleanup()
            if self.health_runner:
                await self.health_runner.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Production Dashboard Server")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level"
    )

    args = parser.parse_args()

    # Create manager
    manager = ProductionDashboardManager(config_file=args.config)

    # Override config with CLI args
    if args.host:
        manager.config["host"] = args.host
    if args.port:
        manager.config["port"] = args.port
    if args.log_level:
        manager.config["log_level"] = args.log_level
        manager._setup_logging()  # Reconfigure logging

    # Start server
    if not await manager.start():
        sys.exit(1)

    try:
        await manager.run_until_shutdown()
    except KeyboardInterrupt:
        pass
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
