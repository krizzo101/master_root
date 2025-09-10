"""Pipeline orchestrator for the unified ingestion system."""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog

from .adapters.chat_adapter import ChatAdapter
from .adapters.code_adapter import CodeAdapter
from .adapters.error_adapter import ErrorAdapter
from .adapters.git_adapter import GitAdapter
from .base_adapter import BaseAdapter
from .config_manager import ConfigManager
from .monitoring import PipelineMonitor
from .pipeline import IngestionPipeline, PipelineConfig
from .registry import AdapterRegistry
from .transformers import DataTransformer

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """Main orchestrator for the unified ingestion pipeline.

    Coordinates all pipeline components:
    - Configuration management
    - Adapter registry and discovery
    - Pipeline execution
    - Monitoring and alerting
    - Graceful shutdown handling
    """

    def __init__(
        self, config_path: Optional[Path] = None, auto_discover_adapters: bool = True
    ):
        """Initialize orchestrator.

        Args:
            config_path: Path to configuration file
            auto_discover_adapters: Whether to auto-discover adapters
        """
        self.config_path = config_path
        self.auto_discover_adapters = auto_discover_adapters

        # Core components
        self.config_manager = ConfigManager(config_path)
        self.registry = AdapterRegistry()
        self.transformer = DataTransformer()
        self.pipeline: Optional[IngestionPipeline] = None
        self.monitor: Optional[PipelineMonitor] = None

        # State management
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._config_watch_task: Optional[asyncio.Task] = None

        # Signal handling
        self._setup_signal_handlers()

        self.logger = logger.bind(component="orchestrator")

    async def initialize(self) -> None:
        """Initialize all pipeline components."""
        self.logger.info("Initializing pipeline orchestrator")

        try:
            # Load configuration
            if self.config_path and self.config_path.exists():
                self.config_manager.load_config(self.config_path)
            else:
                self.logger.info("No config file found, using defaults")

            # Initialize monitoring
            monitoring_config = self.config_manager.get_monitoring_config()
            self.monitor = PipelineMonitor(monitoring_config)
            await self.monitor.start()

            # Register built-in adapters
            await self._register_builtin_adapters()

            # Auto-discover additional adapters
            if self.auto_discover_adapters:
                discovered = self.registry.discover_adapters()
                self.logger.info("Auto-discovered adapters", count=discovered)

            # Create pipeline
            pipeline_config = self.config_manager.get_pipeline_config()
            self.pipeline = IngestionPipeline(
                registry=self.registry,
                transformer=self.transformer,
                config=pipeline_config,
            )

            # Setup adapter configurations
            adapter_configs = self.config_manager.get_adapter_configs()
            for adapter_id, config in adapter_configs.items():
                if adapter_id in [
                    a.config.adapter_id for a in self.registry._adapters.values()
                ]:
                    # Update existing adapter config
                    self.registry._adapter_configs[adapter_id] = config
                else:
                    self.logger.warning(
                        "Configuration found for unknown adapter", adapter_id=adapter_id
                    )

            # Start configuration monitoring
            if self.config_path:
                self._config_watch_task = asyncio.create_task(self._config_watch_loop())

            self.logger.info(
                "Pipeline orchestrator initialized",
                registered_adapters=len(self.registry.list_adapters()),
                config_path=str(self.config_path) if self.config_path else None,
            )

        except Exception as e:
            self.logger.error("Failed to initialize orchestrator", error=str(e))
            await self.cleanup()
            raise

    async def start(
        self, adapter_ids: Optional[List[str]] = None, wait: bool = True
    ) -> None:
        """Start the ingestion pipeline.

        Args:
            adapter_ids: Specific adapters to start (None for all)
            wait: Whether to wait for pipeline completion
        """
        if not self.pipeline:
            raise RuntimeError("Orchestrator not initialized")

        self.logger.info("Starting ingestion pipeline")

        try:
            self._running = True

            # Start the pipeline
            await self.pipeline.start(adapter_ids)

            # Setup monitoring integration
            if self.monitor:
                await self._setup_monitoring_integration()

            self.logger.info("Ingestion pipeline started successfully")

            if wait:
                # Wait for shutdown signal
                await self._shutdown_event.wait()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error("Pipeline startup failed", error=str(e))
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the ingestion pipeline."""
        self.logger.info("Stopping ingestion pipeline")

        self._running = False
        self._shutdown_event.set()

        try:
            # Stop pipeline
            if self.pipeline:
                await self.pipeline.stop()

            # Stop monitoring
            if self.monitor:
                await self.monitor.stop()

            # Stop config watching
            if self._config_watch_task:
                self._config_watch_task.cancel()
                try:
                    await self._config_watch_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Ingestion pipeline stopped")

        except Exception as e:
            self.logger.error("Error during pipeline shutdown", error=str(e))

    async def cleanup(self) -> None:
        """Clean up all resources."""
        await self.stop()

        # Additional cleanup if needed
        if self.registry:
            self.registry.clear_registry()

    @asynccontextmanager
    async def managed_lifecycle(self, adapter_ids: Optional[List[str]] = None):
        """Context manager for complete pipeline lifecycle.

        Args:
            adapter_ids: Specific adapters to start

        Usage:
            async with orchestrator.managed_lifecycle(['chat', 'git']):
                # Pipeline is running
                await do_something()
            # Pipeline is automatically stopped
        """
        try:
            await self.initialize()
            await self.start(adapter_ids, wait=False)
            yield self
        finally:
            await self.cleanup()

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status.

        Returns:
            Complete status information
        """
        status = {
            "orchestrator": {
                "running": self._running,
                "initialized": self.pipeline is not None,
                "config_path": str(self.config_path) if self.config_path else None,
            },
            "registry": self.registry.get_registry_status() if self.registry else {},
            "pipeline": {},
            "monitoring": {},
        }

        if self.pipeline:
            status["pipeline"] = await self.pipeline.get_status()

        if self.monitor:
            status["monitoring"] = await self.monitor.get_monitoring_status()

        return status

    async def pause_adapter(self, adapter_id: str) -> bool:
        """Pause a specific adapter.

        Args:
            adapter_id: ID of adapter to pause

        Returns:
            True if paused successfully
        """
        if self.pipeline:
            return await self.pipeline.pause_adapter(adapter_id)
        return False

    async def resume_adapter(self, adapter_id: str) -> bool:
        """Resume a paused adapter.

        Args:
            adapter_id: ID of adapter to resume

        Returns:
            True if resumed successfully
        """
        if self.pipeline:
            return await self.pipeline.resume_adapter(adapter_id)
        return False

    async def reload_config(self) -> bool:
        """Reload configuration from file.

        Returns:
            True if reloaded successfully
        """
        try:
            if self.config_manager.reload_if_changed():
                # Update pipeline configuration
                if self.pipeline:
                    new_config = self.config_manager.get_pipeline_config()
                    # Update what can be updated at runtime
                    self.pipeline.config = new_config

                # Update adapter configurations
                adapter_configs = self.config_manager.get_adapter_configs()
                for adapter_id, config in adapter_configs.items():
                    if adapter_id in self.registry._adapter_configs:
                        self.registry._adapter_configs[adapter_id] = config

                self.logger.info("Configuration reloaded successfully")
                return True

            return False

        except Exception as e:
            self.logger.error("Failed to reload configuration", error=str(e))
            return False

    def create_template_config(self, output_path: Path) -> None:
        """Create a template configuration file.

        Args:
            output_path: Where to save the template
        """
        self.config_manager.create_template_config(output_path)

    # Private methods

    async def _register_builtin_adapters(self) -> None:
        """Register built-in adapters."""
        builtin_adapters = [
            (ChatAdapter, ChatAdapter.default_config()),
            (CodeAdapter, CodeAdapter.default_config()),
            (GitAdapter, GitAdapter.default_config()),
            (ErrorAdapter, ErrorAdapter.default_config()),
        ]

        for adapter_class, default_config in builtin_adapters:
            try:
                # Get config from config manager or use default
                config = (
                    self.config_manager.get_adapter_config(default_config.adapter_id)
                    or default_config
                )

                self.registry.register_adapter(
                    adapter_id=config.adapter_id,
                    adapter_class=adapter_class,
                    config=config,
                    metadata={"builtin": True},
                )

                self.logger.debug(
                    "Registered builtin adapter", adapter_id=config.adapter_id
                )

            except Exception as e:
                self.logger.error(
                    "Failed to register builtin adapter",
                    adapter_class=adapter_class.__name__,
                    error=str(e),
                )

    async def _setup_monitoring_integration(self) -> None:
        """Setup monitoring integration with pipeline."""
        if not self.monitor or not self.pipeline:
            return

        try:
            # Setup alert handlers
            async def pipeline_alert_handler(alert):
                self.logger.warning(
                    "Pipeline alert",
                    alert_id=alert.id,
                    severity=alert.severity.value,
                    title=alert.title,
                    message=alert.message,
                )

            self.monitor.alerts.add_alert_handler(pipeline_alert_handler)

            # Start collecting pipeline metrics
            asyncio.create_task(self._metrics_collection_loop())

            self.logger.debug("Monitoring integration setup completed")

        except Exception as e:
            self.logger.error("Failed to setup monitoring integration", error=str(e))

    async def _metrics_collection_loop(self) -> None:
        """Collect and report metrics to monitoring system."""
        while self._running and not self._shutdown_event.is_set():
            try:
                if self.monitor and self.pipeline:
                    # Collect pipeline metrics
                    status = await self.pipeline.get_status()

                    # Record pipeline metrics
                    await self.monitor.record_pipeline_metric(
                        "throughput", status["pipeline"].get("average_throughput", 0.0)
                    )

                    await self.monitor.record_pipeline_metric(
                        "items_processed",
                        status["pipeline"].get("total_items_ingested", 0),
                    )

                    await self.monitor.record_pipeline_metric(
                        "items_failed", status["pipeline"].get("total_items_failed", 0)
                    )

                    error_rate = 0.0
                    total_items = status["pipeline"].get("total_items_ingested", 0)
                    failed_items = status["pipeline"].get("total_items_failed", 0)
                    if total_items > 0:
                        error_rate = failed_items / total_items

                    await self.monitor.record_pipeline_metric("error_rate", error_rate)

                    # Record adapter metrics
                    for adapter_id, adapter_status in status.get(
                        "adapters", {}
                    ).items():
                        metrics = adapter_status.get("metrics", {})

                        await self.monitor.record_adapter_metric(
                            adapter_id,
                            "processing_rate",
                            metrics.get("current_processing_rate", 0.0),
                        )

                        await self.monitor.record_adapter_metric(
                            adapter_id,
                            "items_processed",
                            metrics.get("total_items_processed", 0),
                        )

                        await self.monitor.record_adapter_metric(
                            adapter_id,
                            "items_failed",
                            metrics.get("total_items_failed", 0),
                        )

                        if not adapter_status.get("is_healthy", True):
                            await self.monitor.record_adapter_metric(
                                adapter_id, "failures", 1.0
                            )

                await asyncio.sleep(30)  # Collect metrics every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(30)

    async def _config_watch_loop(self) -> None:
        """Monitor configuration file for changes."""
        while self._running and not self._shutdown_event.is_set():
            try:
                if self.config_manager.reload_if_changed():
                    self.logger.info("Configuration file changed, applying updates")

                    # Apply configuration updates
                    await self._apply_config_updates()

                await asyncio.sleep(5)  # Check every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Config watch error", error=str(e))
                await asyncio.sleep(5)

    async def _apply_config_updates(self) -> None:
        """Apply configuration updates to running components."""
        try:
            # Update adapter configurations
            adapter_configs = self.config_manager.get_adapter_configs()
            for adapter_id, config in adapter_configs.items():
                if adapter_id in self.registry._adapter_configs:
                    old_config = self.registry._adapter_configs[adapter_id]
                    self.registry._adapter_configs[adapter_id] = config

                    # Check if adapter needs restart due to config changes
                    if self._config_requires_restart(old_config, config):
                        self.logger.info(
                            "Adapter config requires restart", adapter_id=adapter_id
                        )

                        if self.pipeline:
                            await self.pipeline.pause_adapter(adapter_id)
                            await asyncio.sleep(2)
                            await self.pipeline.resume_adapter(adapter_id)

            # Update monitoring configuration
            if self.monitor:
                monitoring_config = self.config_manager.get_monitoring_config()
                # Apply monitoring config updates if needed
                # This would depend on the monitoring system's capabilities

        except Exception as e:
            self.logger.error("Failed to apply config updates", error=str(e))

    def _config_requires_restart(self, old_config: Any, new_config: Any) -> bool:
        """Check if configuration change requires adapter restart.

        Args:
            old_config: Previous configuration
            new_config: New configuration

        Returns:
            True if restart is required
        """
        # Compare critical configuration fields
        restart_fields = [
            "source_config",
            "batch_mode",
            "max_items_per_second",
            "connection_pool_size",
        ]

        for field in restart_fields:
            if getattr(old_config, field, None) != getattr(new_config, field, None):
                return True

        return False

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info("Received signal, initiating shutdown", signal=signum)
            if self._running:
                # Schedule graceful shutdown
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.stop())
                else:
                    asyncio.run(self.stop())

        # Setup signal handlers on Unix systems
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)


# Convenience functions for common operations


async def create_and_run_pipeline(
    config_path: Optional[Path] = None,
    adapter_ids: Optional[List[str]] = None,
    create_template: bool = False,
) -> None:
    """Create and run pipeline with default settings.

    Args:
        config_path: Path to configuration file
        adapter_ids: Specific adapters to run
        create_template: Create template config and exit
    """
    orchestrator = PipelineOrchestrator(config_path)

    if create_template:
        template_path = config_path or Path("unified_context_config.yaml")
        orchestrator.create_template_config(template_path)
        print(f"Template configuration created: {template_path}")
        return

    try:
        await orchestrator.initialize()
        await orchestrator.start(adapter_ids, wait=True)
    finally:
        await orchestrator.cleanup()


def run_pipeline_cli() -> None:
    """Command-line interface for running the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Context Ingestion Pipeline")
    parser.add_argument("--config", "-c", type=Path, help="Path to configuration file")
    parser.add_argument(
        "--adapters", "-a", nargs="*", help="Specific adapters to run (default: all)"
    )
    parser.add_argument(
        "--template",
        "-t",
        action="store_true",
        help="Create template configuration and exit",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration and exit"
    )

    args = parser.parse_args()

    if args.validate:
        try:
            config_manager = ConfigManager(args.config)
            if args.config:
                config_manager.load_config(args.config)
            print("Configuration is valid")
            return
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            sys.exit(1)

    try:
        asyncio.run(
            create_and_run_pipeline(
                config_path=args.config,
                adapter_ids=args.adapters,
                create_template=args.template,
            )
        )
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline_cli()
