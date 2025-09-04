#!/usr/bin/env python3
"""
Service runner for real-time chat log ingestion system.
Provides service management, configuration, and deployment utilities.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import yaml

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root")

from opsvi_monitoring.chat_analytics.realtime_ingestion.chat_log_watcher import (
    WatcherConfig,
)
from opsvi_monitoring.chat_analytics.realtime_ingestion.fault_tolerance import (
    FaultToleranceManager,
)
from opsvi_monitoring.chat_analytics.realtime_ingestion.monitoring import (
    MonitoringDashboard,
)
from opsvi_monitoring.chat_analytics.realtime_ingestion.realtime_service import (
    RealTimeChatLogService,
    ServiceManager,
)

logger = logging.getLogger(__name__)


class ServiceConfiguration:
    """Manages service configuration from multiple sources."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file and environment."""
        config = self._get_default_config()

        # Load from config file if provided
        if self.config_file and Path(self.config_file).exists():
            file_config = self._load_config_file(self.config_file)
            config.update(file_config)

        # Override with environment variables
        env_config = self._load_env_config()
        config.update(env_config)

        return config

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "service": {
                "name": "realtime-chat-ingestion",
                "log_level": "INFO",
                "log_file": "/tmp/realtime_chat_ingestion.log",
                "pid_file": "/tmp/realtime_chat_ingestion.pid",
                "enable_monitoring": True,
                "enable_fault_tolerance": True,
            },
            "watcher": {
                "enabled": True,
                "batch_size": 10,
                "queue_size": 1000,
                "health_check_interval": 60,
                "watch_interval": 1,
                "max_files_per_minute": 100,
                "file_extensions": [".jsonl"],
                "ignore_patterns": [".tmp", ".backup"],
            },
            "ingestion": {
                "buffer_max_size": 100,
                "buffer_max_age_seconds": 30,
                "correlation_enabled": True,
                "dual_write_enabled": True,
            },
            "database": {
                "sqlite_path": "/home/opsvi/master_root/chat_logs.db",
                "postgres_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "connection_pool_size": 5,
                "query_timeout_seconds": 30,
            },
            "fault_tolerance": {
                "retry_max_attempts": 3,
                "retry_base_delay_seconds": 1.0,
                "retry_max_delay_seconds": 60.0,
                "circuit_breaker_failure_threshold": 5,
                "circuit_breaker_recovery_timeout_seconds": 60,
            },
            "monitoring": {
                "metrics_collection_interval": 60,
                "health_check_interval": 60,
                "dashboard_enabled": True,
                "prometheus_enabled": False,
                "prometheus_port": 9090,
                "alert_enabled": True,
            },
            "discovery": {
                "claude_projects_enabled": True,
                "additional_watch_dirs": [
                    "/home/opsvi/master_root",
                    "/home/opsvi/master_root/apps",
                    "/home/opsvi/master_root/workspace",
                ],
                "exclude_dirs": [".git", "__pycache__", "node_modules", ".venv"],
            },
        }

    def _load_config_file(self, config_path: str) -> Dict:
        """Load configuration from file (JSON or YAML)."""
        try:
            with open(config_path, "r") as f:
                if config_path.endswith((".yml", ".yaml")):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load config file {config_path}: {e}")
            return {}

    def _load_env_config(self) -> Dict:
        """Load configuration from environment variables."""
        env_config = {}

        # Service configuration
        if "CHAT_INGESTION_LOG_LEVEL" in os.environ:
            env_config.setdefault("service", {})["log_level"] = os.environ[
                "CHAT_INGESTION_LOG_LEVEL"
            ]

        # Watcher configuration
        if "CHAT_WATCHER_ENABLED" in os.environ:
            env_config.setdefault("watcher", {})["enabled"] = (
                os.environ["CHAT_WATCHER_ENABLED"].lower() == "true"
            )

        if "CHAT_WATCHER_QUEUE_SIZE" in os.environ:
            env_config.setdefault("watcher", {})["queue_size"] = int(
                os.environ["CHAT_WATCHER_QUEUE_SIZE"]
            )

        # Database configuration
        if "POSTGRES_URL" in os.environ:
            env_config.setdefault("database", {})["postgres_url"] = os.environ[
                "POSTGRES_URL"
            ]

        if "SQLITE_PATH" in os.environ:
            env_config.setdefault("database", {})["sqlite_path"] = os.environ[
                "SQLITE_PATH"
            ]

        return env_config

    def get_watcher_config(self) -> WatcherConfig:
        """Create WatcherConfig from loaded configuration."""
        watcher_config = self.config.get("watcher", {})

        # Set environment variables for WatcherConfig
        os.environ["CHAT_WATCHER_ENABLED"] = str(
            watcher_config.get("enabled", True)
        ).lower()
        os.environ["CHAT_WATCHER_QUEUE_SIZE"] = str(
            watcher_config.get("queue_size", 1000)
        )
        os.environ["CHAT_WATCHER_BATCH_SIZE"] = str(
            watcher_config.get("batch_size", 10)
        )
        os.environ["CHAT_WATCHER_HEALTH_INTERVAL"] = str(
            watcher_config.get("health_check_interval", 60)
        )

        return WatcherConfig()

    def save_config(self, output_path: str):
        """Save current configuration to file."""
        with open(output_path, "w") as f:
            if output_path.endswith((".yml", ".yaml")):
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            else:
                json.dump(self.config, f, indent=2)

        logger.info(f"Configuration saved to {output_path}")


class ServiceRunner:
    """Main service runner with lifecycle management."""

    def __init__(self, config: ServiceConfiguration):
        self.config = config
        self.service = None
        self.monitoring_dashboard = None
        self.fault_tolerance = None
        self.running = False
        self.tasks = []

        # Setup logging
        self._setup_logging()

        # Setup signal handlers
        self._setup_signal_handlers()

    def _setup_logging(self):
        """Setup logging configuration."""
        service_config = self.config.config.get("service", {})
        log_level = service_config.get("log_level", "INFO")
        log_file = service_config.get("log_file", "/tmp/realtime_chat_ingestion.log")

        # Create log directory if needed
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
        )

        # Set specific logger levels
        logging.getLogger("watchdog").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.stop())

    async def start(self):
        """Start all services."""
        if self.running:
            logger.warning("Service runner is already running")
            return

        logger.info("Starting real-time chat log ingestion service runner")
        self.running = True

        try:
            # Write PID file
            self._write_pid_file()

            # Initialize components
            await self._initialize_components()

            # Start all services
            await self._start_services()

            # Wait for shutdown
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in service runner: {e}")
            raise
        finally:
            await self.cleanup()

    async def _initialize_components(self):
        """Initialize all service components."""
        logger.info("Initializing service components")

        # Create watcher config
        watcher_config = self.config.get_watcher_config()

        # Initialize main service
        self.service = RealTimeChatLogService(watcher_config)

        # Initialize monitoring dashboard
        if self.config.config["service"].get("enable_monitoring", True):
            self.monitoring_dashboard = MonitoringDashboard(self.service)

        # Initialize fault tolerance
        if self.config.config["service"].get("enable_fault_tolerance", True):
            self.fault_tolerance = FaultToleranceManager()

    async def _start_services(self):
        """Start all services concurrently."""
        logger.info("Starting all services")

        # Start main service
        main_service_task = asyncio.create_task(
            self.service.start(), name="main_service"
        )
        self.tasks.append(main_service_task)

        # Start monitoring dashboard
        if self.monitoring_dashboard:
            monitoring_task = asyncio.create_task(
                self.monitoring_dashboard.start_monitoring(), name="monitoring"
            )
            self.tasks.append(monitoring_task)

        # Start fault tolerance
        if self.fault_tolerance:
            fault_tolerance_task = asyncio.create_task(
                self.fault_tolerance.start(), name="fault_tolerance"
            )
            self.tasks.append(fault_tolerance_task)

        # Start health check task
        health_check_task = asyncio.create_task(
            self._periodic_health_check(), name="health_check"
        )
        self.tasks.append(health_check_task)

        logger.info(f"Started {len(self.tasks)} service tasks")

    async def _periodic_health_check(self):
        """Periodic health check and status logging."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                if self.monitoring_dashboard:
                    dashboard_data = self.monitoring_dashboard.get_dashboard_data()
                    health_status = dashboard_data.get("health_status", {})

                    logger.info(
                        f"Health Check - "
                        f"Status: {health_status.get('status', 'unknown')}, "
                        f"Uptime: {dashboard_data['service_info']['uptime_seconds']:.0f}s, "
                        f"Queue: {dashboard_data['ingestion_metrics'].get('queue_size', 0)}"
                    )

                    # Export dashboard data periodically
                    export_path = f"/tmp/dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    self.monitoring_dashboard.export_dashboard_data(export_path)

            except Exception as e:
                logger.error(f"Error in health check: {e}")

    async def stop(self):
        """Stop all services gracefully."""
        if not self.running:
            return

        logger.info("Stopping service runner")
        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # Stop individual services
        if self.service:
            await self.service.shutdown()

        if self.monitoring_dashboard:
            self.monitoring_dashboard.stop_monitoring()

        if self.fault_tolerance:
            self.fault_tolerance.stop()

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up resources")

        # Remove PID file
        self._remove_pid_file()

        # Log final status
        if self.monitoring_dashboard:
            final_data = self.monitoring_dashboard.get_dashboard_data()
            logger.info(
                f"Final status - "
                f"Files processed: {final_data['ingestion_metrics'].get('files_processed_per_minute', 0):.1f}/min, "
                f"Uptime: {final_data['service_info']['uptime_seconds']:.0f}s"
            )

    def _write_pid_file(self):
        """Write process ID to file."""
        pid_file = self.config.config["service"].get(
            "pid_file", "/tmp/realtime_chat_ingestion.pid"
        )

        try:
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))
            logger.info(f"PID file written: {pid_file}")
        except Exception as e:
            logger.warning(f"Could not write PID file {pid_file}: {e}")

    def _remove_pid_file(self):
        """Remove PID file."""
        pid_file = self.config.config["service"].get(
            "pid_file", "/tmp/realtime_chat_ingestion.pid"
        )

        try:
            if Path(pid_file).exists():
                os.unlink(pid_file)
                logger.info(f"PID file removed: {pid_file}")
        except Exception as e:
            logger.warning(f"Could not remove PID file {pid_file}: {e}")

    def get_status(self) -> Dict:
        """Get service status."""
        status = {
            "running": self.running,
            "tasks": len(self.tasks),
            "config": self.config.config,
        }

        if self.service:
            status["service"] = self.service.get_health_status()

        if self.monitoring_dashboard:
            status["monitoring"] = self.monitoring_dashboard.get_dashboard_data()

        return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Real-time chat log ingestion service")
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "config"],
        help="Service command",
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--daemon", "-d", action="store_true", help="Run as daemon (background process)"
    )
    parser.add_argument("--pid-file", help="Custom PID file path")
    parser.add_argument("--log-level", help="Override log level")
    parser.add_argument("--export-config", help="Export current config to file")

    args = parser.parse_args()

    # Load configuration
    config = ServiceConfiguration(args.config)

    # Override config with CLI args
    if args.pid_file:
        config.config["service"]["pid_file"] = args.pid_file
    if args.log_level:
        config.config["service"]["log_level"] = args.log_level

    # Handle commands
    if args.command == "config":
        if args.export_config:
            config.save_config(args.export_config)
            print(f"Configuration exported to {args.export_config}")
        else:
            print(json.dumps(config.config, indent=2))
        return

    elif args.command == "status":
        pid_file = config.config["service"]["pid_file"]
        if Path(pid_file).exists():
            with open(pid_file) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if process exists
                print(f"Service is running (PID: {pid})")
            except OSError:
                print("Service is not running (stale PID file)")
        else:
            print("Service is not running")
        return

    elif args.command in ["stop", "restart"]:
        # Send SIGTERM to running process
        pid_file = config.config["service"]["pid_file"]
        if Path(pid_file).exists():
            with open(pid_file) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Stop signal sent to process {pid}")

                # Wait for process to stop
                import time

                for _ in range(30):  # Wait up to 30 seconds
                    try:
                        os.kill(pid, 0)
                        time.sleep(1)
                    except OSError:
                        break
                else:
                    print("Process did not stop gracefully, sending SIGKILL")
                    os.kill(pid, signal.SIGKILL)

            except OSError:
                print("Service was not running")

        if args.command == "stop":
            return

    # Start service
    if args.command in ["start", "restart"]:
        if args.daemon:
            # Fork to background
            if os.fork() == 0:
                os.setsid()
                if os.fork() == 0:
                    # Run service in background
                    runner = ServiceRunner(config)
                    try:
                        asyncio.run(runner.start())
                    except KeyboardInterrupt:
                        print("Service interrupted")
                    except Exception as e:
                        print(f"Service error: {e}")
                        sys.exit(1)
        else:
            # Run in foreground
            runner = ServiceRunner(config)
            try:
                asyncio.run(runner.start())
            except KeyboardInterrupt:
                print("\nService interrupted")
            except Exception as e:
                print(f"Service error: {e}")
                sys.exit(1)


if __name__ == "__main__":
    main()
