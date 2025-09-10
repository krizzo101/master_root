#!/usr/bin/env python3
"""
Real-time chat log ingestion service.
Combines file watching with ingestion pipeline for immediate processing.
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import uvloop  # For better async performance

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root")

from opsvi_monitoring.chat_analytics.realtime_ingestion.chat_log_watcher import (
    ChatLogDiscovery,
    ChatLogWatcher,
    WatcherConfig,
    WatcherHealthCheck,
)
from opsvi_monitoring.chat_analytics.realtime_ingestion.ingestion_pipeline import (
    IngestionCoordinator,
)

logger = logging.getLogger(__name__)


class RealTimeChatLogService:
    """Main real-time chat log ingestion service."""

    def __init__(self, config: Optional[WatcherConfig] = None):
        self.config = config or WatcherConfig()
        self.running = False
        self.start_time = None

        # Core components
        self.discovery = ChatLogDiscovery()
        self.health_check = WatcherHealthCheck()
        self.ingestion_queue = asyncio.Queue(maxsize=self.config.queue_size)
        self.coordinator = IngestionCoordinator()
        self.watcher = None

        # Statistics and monitoring
        self.stats = {
            "service_starts": 0,
            "files_queued": 0,
            "processing_errors": 0,
            "last_health_check": None,
        }

        # Graceful shutdown handling
        self.shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())

    async def start(self):
        """Start the real-time chat log service."""
        if self.running:
            logger.warning("Service is already running")
            return

        logger.info("Starting real-time chat log ingestion service")
        self.running = True
        self.start_time = time.time()
        self.stats["service_starts"] += 1

        try:
            # Discover watch directories
            watch_directories = self.discovery.discover_watch_directories()
            logger.info(f"Will monitor {len(watch_directories)} directories")

            # Initialize watcher
            self.watcher = ChatLogWatcher(watch_directories, self.ingestion_queue)

            # Start all components
            await asyncio.gather(
                self._run_watcher(),
                self._run_coordinator(),
                self._run_queue_processor(),
                self._run_health_monitor(),
                self._wait_for_shutdown(),
            )

        except Exception as e:
            logger.error(f"Error starting service: {e}")
            await self.shutdown()
            raise

    async def _run_watcher(self):
        """Run the file watcher in a separate thread."""
        try:
            # Start watcher (runs in separate thread)
            self.watcher.start()

            # Keep running until shutdown
            while self.running and not self.shutdown_event.is_set():
                await asyncio.sleep(1)

        finally:
            if self.watcher:
                self.watcher.stop()

    async def _run_coordinator(self):
        """Run the ingestion coordinator."""
        try:
            # Connect coordinator to our queue
            self.coordinator.file_queue = self.ingestion_queue
            await self.coordinator.start()

        except Exception as e:
            logger.error(f"Error in coordinator: {e}")
            self.stats["processing_errors"] += 1

    async def _run_queue_processor(self):
        """Process files from the ingestion queue."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Monitor queue size for backpressure
                queue_size = self.ingestion_queue.qsize()
                if queue_size > self.config.queue_size * 0.8:
                    logger.warning(
                        f"Ingestion queue near capacity: {queue_size}/{self.config.queue_size}"
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(5)

    async def _run_health_monitor(self):
        """Monitor service health and log statistics."""
        while self.running and not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)

                health_status = self.get_health_status()
                self.stats["last_health_check"] = datetime.now().isoformat()

                # Log health summary
                logger.info(
                    f"Health Check - "
                    f"Uptime: {health_status['uptime_minutes']:.1f}min, "
                    f"Files processed: {health_status['files_processed']}, "
                    f"Queue size: {health_status['queue_size']}, "
                    f"Healthy: {health_status['is_healthy']}"
                )

                # Log warnings if unhealthy
                if not health_status["is_healthy"]:
                    logger.warning("Service appears unhealthy - investigating")

            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()

    async def shutdown(self):
        """Gracefully shutdown the service."""
        if not self.running:
            return

        logger.info("Shutting down real-time chat log service")
        self.running = False
        self.shutdown_event.set()

        try:
            # Stop watcher
            if self.watcher:
                self.watcher.stop()

            # Stop coordinator
            if self.coordinator:
                await self.coordinator.stop()

            # Final health check
            final_status = self.get_health_status()
            logger.info(f"Service shutdown complete. Final stats: {final_status}")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def get_health_status(self) -> Dict:
        """Get comprehensive health status."""
        uptime = time.time() - self.start_time if self.start_time else 0

        base_status = {
            "service_running": self.running,
            "uptime_seconds": uptime,
            "uptime_minutes": uptime / 60,
            "queue_size": self.ingestion_queue.qsize(),
            "queue_capacity": self.config.queue_size,
            "stats": self.stats,
        }

        # Add watcher health
        if hasattr(self, "health_check"):
            watcher_health = self.health_check.get_status()
            base_status.update(
                {
                    "watcher_health": watcher_health,
                    "files_processed": watcher_health["files_processed"],
                    "is_healthy": watcher_health["is_healthy"] and self.running,
                }
            )

        # Add coordinator status
        if self.coordinator:
            coordinator_status = self.coordinator.get_status()
            base_status["coordinator"] = coordinator_status

        return base_status

    async def process_file_immediately(self, file_path: str):
        """Process a specific file immediately (for testing/manual triggers)."""
        if not self.running:
            raise RuntimeError("Service is not running")

        file_info = {
            "path": file_path,
            "event_type": "manual",
            "timestamp": datetime.now().isoformat(),
            "size": Path(file_path).stat().st_size if Path(file_path).exists() else 0,
        }

        await self.ingestion_queue.put(file_info)
        logger.info(f"Queued file for immediate processing: {file_path}")


class ServiceManager:
    """Manages the real-time service lifecycle."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.service = None
        self.config = None
        self._load_config()

    def _load_config(self):
        """Load configuration from file or environment."""
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file) as f:
                    config_data = json.load(f)
                # Apply config_data to environment or create custom config
                self.config = WatcherConfig()
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Could not load config from {self.config_file}: {e}")
                self.config = WatcherConfig()
        else:
            self.config = WatcherConfig()

    async def run(self):
        """Run the service with proper async setup."""
        if not self.config.watch_enabled:
            logger.info("Chat log watching is disabled by configuration")
            return

        # Use uvloop for better performance on Linux
        if sys.platform != "win32":
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        # Create and run service
        self.service = RealTimeChatLogService(self.config)

        try:
            await self.service.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")
        finally:
            if self.service:
                await self.service.shutdown()

    def run_sync(self):
        """Synchronous entry point."""
        asyncio.run(self.run())


# CLI and standalone execution
def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("/tmp/realtime_chat_ingestion.log"),
        ],
    )


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Real-time chat log ingestion service")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--test-file", help="Test with specific file")

    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.test_file:
        # Test mode - process single file
        service = RealTimeChatLogService()
        await service.start()
        await service.process_file_immediately(args.test_file)
        await asyncio.sleep(5)  # Give time to process
        await service.shutdown()
    else:
        # Normal service mode
        manager = ServiceManager(args.config)
        await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
