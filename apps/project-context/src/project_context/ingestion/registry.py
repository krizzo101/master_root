"""Adapter registry for plugin management."""

import importlib
import inspect
from typing import Any, Dict, List, Optional, Set, Type

import structlog

from .base_adapter import AdapterConfig, BaseAdapter

logger = structlog.get_logger(__name__)


class AdapterRegistry:
    """Registry for managing ingestion adapters.

    Provides plugin-style registration and discovery of adapters.
    Supports both programmatic registration and automatic discovery.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseAdapter]] = {}
        self._adapter_configs: Dict[str, AdapterConfig] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

        self.logger = logger.bind(component="adapter_registry")

    def register_adapter(
        self,
        adapter_id: str,
        adapter_class: Type[BaseAdapter],
        config: AdapterConfig,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an adapter class.

        Args:
            adapter_id: Unique identifier for the adapter
            adapter_class: Adapter class (must inherit from BaseAdapter)
            config: Configuration for the adapter
            metadata: Optional metadata about the adapter

        Raises:
            ValueError: If adapter_id already registered or class invalid
        """
        if adapter_id in self._adapter_classes:
            raise ValueError(f"Adapter '{adapter_id}' already registered")

        if not issubclass(adapter_class, BaseAdapter):
            raise ValueError(f"Adapter class must inherit from BaseAdapter")

        self._adapter_classes[adapter_id] = adapter_class
        self._adapter_configs[adapter_id] = config
        self._metadata[adapter_id] = metadata or {}

        self.logger.info(
            "Adapter registered",
            adapter_id=adapter_id,
            adapter_class=adapter_class.__name__,
            source_type=config.source_type,
        )

    def unregister_adapter(self, adapter_id: str) -> bool:
        """Unregister an adapter.

        Args:
            adapter_id: ID of adapter to unregister

        Returns:
            True if adapter was unregistered, False if not found
        """
        if adapter_id not in self._adapter_classes:
            return False

        # Clean up all references
        del self._adapter_classes[adapter_id]
        del self._adapter_configs[adapter_id]
        del self._metadata[adapter_id]

        if adapter_id in self._adapters:
            del self._adapters[adapter_id]

        self.logger.info("Adapter unregistered", adapter_id=adapter_id)
        return True

    def get_adapter(self, adapter_id: str) -> Optional[BaseAdapter]:
        """Get or create an adapter instance.

        Args:
            adapter_id: ID of adapter to get

        Returns:
            Adapter instance or None if not found
        """
        # Return existing instance if available
        if adapter_id in self._adapters:
            return self._adapters[adapter_id]

        # Create new instance if class registered
        if adapter_id in self._adapter_classes:
            try:
                adapter_class = self._adapter_classes[adapter_id]
                config = self._adapter_configs[adapter_id]

                adapter = adapter_class(config)
                self._adapters[adapter_id] = adapter

                self.logger.info("Adapter instance created", adapter_id=adapter_id)

                return adapter

            except Exception as e:
                self.logger.error(
                    "Failed to create adapter instance",
                    adapter_id=adapter_id,
                    error=str(e),
                )
                return None

        return None

    def list_adapters(self) -> List[str]:
        """List all registered adapter IDs.

        Returns:
            List of adapter IDs
        """
        return list(self._adapter_classes.keys())

    def get_adapters_by_source_type(self, source_type: str) -> List[str]:
        """Get adapters for a specific source type.

        Args:
            source_type: Source type to filter by

        Returns:
            List of adapter IDs for the source type
        """
        matching_adapters = []

        for adapter_id, config in self._adapter_configs.items():
            if config.source_type == source_type:
                matching_adapters.append(adapter_id)

        return matching_adapters

    def get_adapter_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered adapter.

        Args:
            adapter_id: ID of adapter to get info for

        Returns:
            Dictionary with adapter information or None if not found
        """
        if adapter_id not in self._adapter_classes:
            return None

        adapter_class = self._adapter_classes[adapter_id]
        config = self._adapter_configs[adapter_id]
        metadata = self._metadata[adapter_id]

        # Get instance status if available
        instance_status = None
        if adapter_id in self._adapters:
            adapter = self._adapters[adapter_id]
            instance_status = {
                "status": adapter.status.value,
                "is_healthy": adapter.is_healthy,
                "metrics": {
                    "total_items_processed": adapter.metrics.total_items_processed,
                    "total_items_failed": adapter.metrics.total_items_failed,
                    "current_processing_rate": adapter.metrics.current_processing_rate,
                },
            }

        return {
            "adapter_id": adapter_id,
            "class_name": adapter_class.__name__,
            "module": adapter_class.__module__,
            "source_type": config.source_type,
            "version": config.version,
            "batch_mode": config.batch_mode.value,
            "batch_size": config.batch_size,
            "enabled_features": list(config.enabled_features),
            "metadata": metadata,
            "instance_status": instance_status,
        }

    def validate_adapters(self) -> Dict[str, Any]:
        """Validate all registered adapters.

        Returns:
            Dictionary with validation results
        """
        results = {
            "total_adapters": len(self._adapter_classes),
            "valid_adapters": [],
            "invalid_adapters": [],
            "validation_errors": [],
        }

        for adapter_id in self._adapter_classes:
            try:
                adapter_class = self._adapter_classes[adapter_id]
                config = self._adapter_configs[adapter_id]

                # Check that class properly implements required methods
                required_methods = [
                    "initialize",
                    "fetch_items",
                    "transform_item",
                    "cleanup",
                ]

                for method_name in required_methods:
                    if not hasattr(adapter_class, method_name):
                        raise ValueError(f"Missing required method: {method_name}")

                    method = getattr(adapter_class, method_name)
                    if not callable(method):
                        raise ValueError(f"Method not callable: {method_name}")

                # Validate configuration
                if not config.adapter_id or not config.source_type:
                    raise ValueError("Configuration missing required fields")

                results["valid_adapters"].append(adapter_id)

            except Exception as e:
                results["invalid_adapters"].append(adapter_id)
                results["validation_errors"].append(
                    {"adapter_id": adapter_id, "error": str(e)}
                )

                self.logger.error(
                    "Adapter validation failed", adapter_id=adapter_id, error=str(e)
                )

        return results

    def discover_adapters(
        self, package_name: str = "project_context.ingestion.adapters"
    ) -> int:
        """Automatically discover and register adapters.

        Args:
            package_name: Python package to search for adapters

        Returns:
            Number of adapters discovered and registered
        """
        discovered_count = 0

        try:
            # Import the package
            package = importlib.import_module(package_name)

            # Get all classes from the package
            for name, obj in inspect.getmembers(package, inspect.isclass):
                # Skip if not a subclass of BaseAdapter
                if not issubclass(obj, BaseAdapter) or obj is BaseAdapter:
                    continue

                # Skip if already registered
                if any(cls is obj for cls in self._adapter_classes.values()):
                    continue

                # Try to create a default configuration
                try:
                    # Look for a default config method or attribute
                    if hasattr(obj, "default_config"):
                        if callable(obj.default_config):
                            config = obj.default_config()
                        else:
                            config = obj.default_config
                    else:
                        # Create basic config based on class name
                        adapter_id = name.lower().replace("adapter", "")
                        config = AdapterConfig(
                            adapter_id=adapter_id, source_type=adapter_id
                        )

                    # Register the adapter
                    self.register_adapter(
                        adapter_id=config.adapter_id,
                        adapter_class=obj,
                        config=config,
                        metadata={"discovered": True},
                    )

                    discovered_count += 1

                except Exception as e:
                    self.logger.warning(
                        "Failed to auto-register discovered adapter",
                        adapter_class=name,
                        error=str(e),
                    )

        except ImportError as e:
            self.logger.warning(
                "Failed to import adapter package",
                package_name=package_name,
                error=str(e),
            )

        except Exception as e:
            self.logger.error(
                "Adapter discovery failed", package_name=package_name, error=str(e)
            )

        self.logger.info(
            "Adapter discovery completed",
            discovered_count=discovered_count,
            total_registered=len(self._adapter_classes),
        )

        return discovered_count

    def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status.

        Returns:
            Registry status information
        """
        # Count adapters by source type
        source_type_counts = {}
        for config in self._adapter_configs.values():
            source_type = config.source_type
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

        # Count adapters by status
        status_counts = {
            "not_instantiated": 0,
            "idle": 0,
            "running": 0,
            "paused": 0,
            "error": 0,
            "shutdown": 0,
        }

        for adapter_id, config in self._adapter_configs.items():
            if adapter_id in self._adapters:
                status = self._adapters[adapter_id].status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            else:
                status_counts["not_instantiated"] += 1

        return {
            "total_registered": len(self._adapter_classes),
            "total_instantiated": len(self._adapters),
            "source_type_counts": source_type_counts,
            "status_counts": status_counts,
            "adapters": list(self._adapter_classes.keys()),
        }

    def clear_registry(self) -> None:
        """Clear all registered adapters.

        Warning: This will remove all adapters from the registry.
        Any running adapters should be stopped first.
        """
        self.logger.warning("Clearing adapter registry")

        self._adapter_classes.clear()
        self._adapter_configs.clear()
        self._metadata.clear()
        self._adapters.clear()

    def export_config(self) -> Dict[str, Any]:
        """Export adapter configurations.

        Returns:
            Dictionary containing all adapter configurations
        """
        exported_config = {}

        for adapter_id, config in self._adapter_configs.items():
            exported_config[adapter_id] = {
                "adapter_id": config.adapter_id,
                "source_type": config.source_type,
                "version": config.version,
                "batch_mode": config.batch_mode.value,
                "batch_size": config.batch_size,
                "batch_timeout_seconds": config.batch_timeout_seconds,
                "max_items_per_second": config.max_items_per_second,
                "max_concurrent_batches": config.max_concurrent_batches,
                "max_retries": config.max_retries,
                "retry_delay_seconds": config.retry_delay_seconds,
                "retry_backoff_factor": config.retry_backoff_factor,
                "strict_validation": config.strict_validation,
                "skip_duplicates": config.skip_duplicates,
                "content_hash_check": config.content_hash_check,
                "generate_embeddings": config.generate_embeddings,
                "generate_summaries": config.generate_summaries,
                "extract_relationships": config.extract_relationships,
                "source_config": config.source_config,
                "enabled_features": list(config.enabled_features),
                "disabled_features": list(config.disabled_features),
            }

        return exported_config

    def import_config(self, config_data: Dict[str, Any]) -> int:
        """Import adapter configurations.

        Args:
            config_data: Configuration dictionary from export_config()

        Returns:
            Number of configurations imported
        """
        imported_count = 0

        for adapter_id, config_dict in config_data.items():
            try:
                # Create AdapterConfig from dictionary
                config = AdapterConfig(
                    adapter_id=config_dict["adapter_id"],
                    source_type=config_dict["source_type"],
                    version=config_dict.get("version", "1.0"),
                    batch_mode=BatchMode(config_dict.get("batch_mode", "streaming")),
                    batch_size=config_dict.get("batch_size", 100),
                    # ... other fields would be mapped here
                )

                # Update existing config or skip if adapter not registered
                if adapter_id in self._adapter_configs:
                    self._adapter_configs[adapter_id] = config
                    imported_count += 1

                    self.logger.info("Configuration imported", adapter_id=adapter_id)

            except Exception as e:
                self.logger.error(
                    "Failed to import configuration",
                    adapter_id=adapter_id,
                    error=str(e),
                )

        return imported_count
