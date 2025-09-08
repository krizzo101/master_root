#!/usr/bin/env python3
"""
Real-time Chat Log Service
Integrates file watching with PostgreSQL ingestion for real-time chat analytics.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import List

# Add necessary paths
sys.path.append("/home/opsvi/master_root/libs/opsvi-monitoring")
sys.path.append("/home/opsvi/master_root/libs")

from opsvi_monitoring.chat_analytics.realtime_ingestion.chat_log_watcher import (
    ChatLogDiscovery,
    ChatLogWatcher,
    WatcherConfig,
    WatcherHealthCheck,
)
from opsvi_monitoring.chat_analytics.realtime_ingestion.postgres_chat_ingester import (
    PostgresChatIngestionService,
)

logger = logging.getLogger(__name__)


class RealtimeChatService:
    """
    Complete real-time chat log processing service.
    Combines file watching with PostgreSQL ingestion.
    """

    def __init__(self):
        self.config = WatcherConfig()
        self.discovery = ChatLogDiscovery()
        self.health_check = WatcherHealthCheck()

        # Components
        self.watcher = None
        self.ingestion_service = PostgresChatIngestionService()

        # Service state
        self.running = False
        self.ingestion_task = None

    async def start(self, watch_directories: List[str] = None):
        """Start the complete real-time service."""
        logger.info("Starting Real-time Chat Log Service")

        # Discover watch directories if not provided
        if watch_directories is None:
            watch_directories = self.discovery.discover_watch_directories()
            logger.info(f"Auto-discovered {len(watch_directories)} watch directories")

        # Start PostgreSQL ingestion service
        logger.info("Starting PostgreSQL ingestion service...")
        self.ingestion_task = await self.ingestion_service.start(watch_directories)

        # Start file watcher
        logger.info("Starting file watcher...")
        self.watcher = ChatLogWatcher(
            watch_directories=watch_directories,
            ingestion_queue=self.ingestion_service.file_queue,
        )
        self.watcher.start()

        self.running = True
        logger.info("Real-time Chat Service started successfully")

        # Service monitoring loop
        await self._run_service_loop()

    async def _run_service_loop(self):
        """Main service monitoring loop."""
        while self.running:
            try:
                # Health check
                self.health_check.record_activity()

                # Log stats periodically
                stats = await self.ingestion_service.ingester.get_ingestion_stats()
                logger.info(f"Service stats: {stats}")

                # Sleep
                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Service loop error: {e}")
                self.health_check.record_error(str(e))
                await asyncio.sleep(10)  # Error backoff

    async def stop(self):
        """Stop the service gracefully."""
        logger.info("Stopping Real-time Chat Service")
        self.running = False

        # Stop file watcher
        if self.watcher:
            self.watcher.stop()

        # Stop ingestion service
        await self.ingestion_service.stop()

        # Cancel ingestion task
        if self.ingestion_task and not self.ingestion_task.done():
            self.ingestion_task.cancel()

        logger.info("Real-time Chat Service stopped")

    def get_service_status(self):
        """Get current service status."""
        return {
            "running": self.running,
            "watcher_active": self.watcher and self.watcher.running,
            "health": self.health_check.get_status(),
            "watch_directories": len(self.watcher.watch_directories)
            if self.watcher
            else 0,
            "queue_size": self.ingestion_service.file_queue.qsize(),
        }


class ServiceManager:
    """Manages the real-time service with proper signal handling."""

    def __init__(self):
        self.service = RealtimeChatService()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.service.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self, watch_directories: List[str] = None):
        """Run the service with proper signal handling."""
        self.setup_signal_handlers()

        try:
            await self.service.start(watch_directories)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            await self.service.stop()


# CLI Interface
async def main():
    """Main entry point for the service."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Real-time Chat Log Processing Service"
    )
    parser.add_argument(
        "--watch-dirs", nargs="+", help="Directories to watch for chat logs"
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (process existing files and exit)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("/home/opsvi/master_root/realtime_chat_service.log"),
        ],
    )

    # Create and run service
    if args.test:
        # Test mode - process existing files and exit
        logger.info("Running in test mode")
        service = PostgresChatIngestionService()

        watch_dirs = args.watch_dirs or ["/home/opsvi/.claude/session-exports"]
        await service.start(watch_dirs)
        await service.stop()

        logger.info("Test complete")
    else:
        # Production mode - run continuously
        manager = ServiceManager()
        await manager.run(args.watch_dirs)


if __name__ == "__main__":
    # Run the service
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
