"""Configuration management for the ingestion pipeline."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
import yaml

from .base_adapter import AdapterConfig, BatchMode
from .monitoring import PipelineMonitor
from .pipeline import PipelineConfig

logger = structlog.get_logger(__name__)


class ConfigurationError(Exception):
    """Configuration-related error."""

    pass


class ConfigManager:
    """Centralized configuration management for the ingestion pipeline.

    Supports:
    - YAML and JSON configuration files
    - Environment variable overrides
    - Configuration validation
    - Hot-reloading of configurations
    - Configuration templates and presets
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to main configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config_data: Dict[str, Any] = {}
        self.last_modified: Optional[datetime] = None
        self.logger = logger.bind(component="config_manager")

        # Default configurations
        self._default_pipeline_config = self._get_default_pipeline_config()
        self._default_adapter_configs = self._get_default_adapter_configs()

        # Load configuration if path provided
        if self.config_path and self.config_path.exists():
            self.load_config()

    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Load configuration from file.

        Args:
            config_path: Override default config path
        """
        if config_path:
            self.config_path = Path(config_path)

        if not self.config_path or not self.config_path.exists():
            self.logger.warning("No configuration file found, using defaults")
            self._load_default_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    self.config_data = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == ".json":
                    self.config_data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported config format: {self.config_path.suffix}"
                    )

            # Apply environment variable overrides
            self._apply_env_overrides()

            # Validate configuration
            self._validate_config()

            # Track file modification time
            self.last_modified = datetime.fromtimestamp(
                self.config_path.stat().st_mtime
            )

            self.logger.info(
                "Configuration loaded successfully",
                config_path=str(self.config_path),
                adapters=len(self.config_data.get("adapters", {})),
            )

        except Exception as e:
            self.logger.error(
                "Failed to load configuration",
                config_path=str(self.config_path),
                error=str(e),
            )
            raise ConfigurationError(f"Configuration load failed: {e}")

    def save_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Save current configuration to file.

        Args:
            config_path: Override default config path
        """
        if config_path:
            self.config_path = Path(config_path)

        if not self.config_path:
            raise ConfigurationError("No config path specified for saving")

        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(
                        self.config_data,
                        f,
                        default_flow_style=False,
                        sort_keys=True,
                        indent=2,
                    )
                else:
                    json.dump(
                        self.config_data,
                        f,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                    )

            self.logger.info("Configuration saved", config_path=str(self.config_path))

        except Exception as e:
            self.logger.error(
                "Failed to save configuration",
                config_path=str(self.config_path),
                error=str(e),
            )
            raise ConfigurationError(f"Configuration save failed: {e}")

    def get_pipeline_config(self) -> PipelineConfig:
        """Get pipeline configuration object."""
        pipeline_config = self.config_data.get("pipeline", {})

        # Apply defaults and create PipelineConfig
        config_kwargs = {}

        # Map configuration keys to PipelineConfig parameters
        config_mapping = {
            "max_concurrent_adapters": "max_concurrent_adapters",
            "batch_commit_size": "batch_commit_size",
            "health_check_interval": "health_check_interval",
            "metrics_collection_interval": "metrics_collection_interval",
            "auto_restart_failed_adapters": "auto_restart_failed_adapters",
            "adapter_failure_backoff_seconds": "adapter_failure_backoff_seconds",
            "pipeline_shutdown_timeout_seconds": "pipeline_shutdown_timeout_seconds",
            "database_url": "database_url",
            "database_pool_min": "database_pool_min",
            "database_pool_max": "database_pool_max",
            "database_command_timeout": "database_command_timeout",
            "max_retry_attempts": "max_retry_attempts",
            "retry_base_delay": "retry_base_delay",
            "retry_max_delay": "retry_max_delay",
            "retry_exponential_base": "retry_exponential_base",
            "enable_relationship_detection": "enable_relationship_detection",
            "relationship_context_window_size": "relationship_context_window_size",
            "relationship_batch_size": "relationship_batch_size",
            "enable_memory_monitoring": "enable_memory_monitoring",
            "max_pipeline_memory_mb": "max_pipeline_memory_mb",
            "gc_interval_seconds": "gc_interval_seconds",
            "enable_duplicate_detection": "enable_duplicate_detection",
            "enable_content_validation": "enable_content_validation",
            "min_content_length": "min_content_length",
            "max_content_length": "max_content_length",
        }

        for config_key, param_name in config_mapping.items():
            if config_key in pipeline_config:
                config_kwargs[param_name] = pipeline_config[config_key]

        return PipelineConfig(**config_kwargs)

    def get_adapter_configs(self) -> Dict[str, AdapterConfig]:
        """Get all adapter configurations."""
        adapter_configs = {}
        adapters_config = self.config_data.get("adapters", {})

        for adapter_id, adapter_config in adapters_config.items():
            try:
                config = self._create_adapter_config(adapter_id, adapter_config)
                adapter_configs[adapter_id] = config
            except Exception as e:
                self.logger.error(
                    "Failed to create adapter config",
                    adapter_id=adapter_id,
                    error=str(e),
                )

        return adapter_configs

    def get_adapter_config(self, adapter_id: str) -> Optional[AdapterConfig]:
        """Get configuration for a specific adapter.

        Args:
            adapter_id: ID of the adapter

        Returns:
            AdapterConfig or None if not found
        """
        adapters_config = self.config_data.get("adapters", {})
        adapter_config = adapters_config.get(adapter_id)

        if not adapter_config:
            return None

        try:
            return self._create_adapter_config(adapter_id, adapter_config)
        except Exception as e:
            self.logger.error(
                "Failed to create adapter config", adapter_id=adapter_id, error=str(e)
            )
            return None

    def set_adapter_config(self, adapter_id: str, config: AdapterConfig) -> None:
        """Set configuration for an adapter.

        Args:
            adapter_id: ID of the adapter
            config: AdapterConfig object
        """
        if "adapters" not in self.config_data:
            self.config_data["adapters"] = {}

        self.config_data["adapters"][adapter_id] = {
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
            "health_check_interval_seconds": config.health_check_interval_seconds,
            "error_threshold_count": config.error_threshold_count,
            "error_threshold_window_seconds": config.error_threshold_window_seconds,
            "strict_validation": config.strict_validation,
            "skip_duplicates": config.skip_duplicates,
            "content_hash_check": config.content_hash_check,
            "generate_embeddings": config.generate_embeddings,
            "generate_summaries": config.generate_summaries,
            "extract_relationships": config.extract_relationships,
            "source_config": config.source_config,
            "enabled_features": list(config.enabled_features),
            "disabled_features": list(config.disabled_features),
            "circuit_breaker_threshold": config.circuit_breaker_threshold,
            "circuit_breaker_timeout_seconds": config.circuit_breaker_timeout_seconds,
            "circuit_breaker_reset_threshold": config.circuit_breaker_reset_threshold,
            "connection_pool_size": config.connection_pool_size,
            "connection_timeout_seconds": config.connection_timeout_seconds,
            "max_memory_mb": config.max_memory_mb,
            "memory_check_interval_seconds": config.memory_check_interval_seconds,
        }

        self.logger.info("Adapter configuration updated", adapter_id=adapter_id)

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.config_data.get(
            "monitoring",
            {
                "metrics_retention_hours": 24,
                "max_metrics_per_name": 10000,
                "max_alerts": 1000,
                "enable_system_metrics": True,
                "alert_handlers": [],
            },
        )

    def check_for_updates(self) -> bool:
        """Check if configuration file has been updated.

        Returns:
            True if file has been modified since last load
        """
        if not self.config_path or not self.config_path.exists():
            return False

        try:
            current_mtime = datetime.fromtimestamp(self.config_path.stat().st_mtime)

            if self.last_modified and current_mtime > self.last_modified:
                return True

            return False

        except Exception as e:
            self.logger.error("Error checking config file updates", error=str(e))
            return False

    def reload_if_changed(self) -> bool:
        """Reload configuration if file has changed.

        Returns:
            True if configuration was reloaded
        """
        if self.check_for_updates():
            try:
                self.load_config()
                self.logger.info("Configuration reloaded due to file changes")
                return True
            except Exception as e:
                self.logger.error("Failed to reload configuration", error=str(e))

        return False

    def create_template_config(self, output_path: Union[str, Path]) -> None:
        """Create a template configuration file.

        Args:
            output_path: Path where to save the template
        """
        template_config = {
            "pipeline": {
                "max_concurrent_adapters": 10,
                "batch_commit_size": 1000,
                "health_check_interval": 60,
                "metrics_collection_interval": 30,
                "auto_restart_failed_adapters": True,
                "adapter_failure_backoff_seconds": 300,
                "pipeline_shutdown_timeout_seconds": 60,
                "database_url": "postgresql://user:pass@localhost:5432/unified_context",
                "database_pool_min": 5,
                "database_pool_max": 20,
                "database_command_timeout": 60,
                "max_retry_attempts": 3,
                "retry_base_delay": 1.0,
                "retry_max_delay": 60.0,
                "retry_exponential_base": 2.0,
                "enable_relationship_detection": True,
                "relationship_context_window_size": 100,
                "relationship_batch_size": 50,
                "enable_memory_monitoring": True,
                "max_pipeline_memory_mb": 2048,
                "gc_interval_seconds": 300,
                "enable_duplicate_detection": True,
                "enable_content_validation": True,
                "min_content_length": 1,
                "max_content_length": 1000000,
            },
            "adapters": {
                "chat": {
                    "source_type": "chat",
                    "version": "1.0",
                    "batch_mode": "streaming",
                    "batch_size": 50,
                    "generate_embeddings": True,
                    "generate_summaries": False,
                    "extract_relationships": True,
                    "source_config": {
                        "input_format": "jsonl",
                        "file_patterns": ["*.jsonl", "*.json"],
                        "watch_directories": ["."],
                        "include_system_messages": True,
                        "conversation_timeout_minutes": 60,
                    },
                },
                "code": {
                    "source_type": "code",
                    "version": "1.0",
                    "batch_mode": "batch",
                    "batch_size": 100,
                    "generate_embeddings": True,
                    "extract_relationships": True,
                    "source_config": {
                        "scan_directories": ["."],
                        "include_patterns": ["*.py", "*.js", "*.ts", "*.java"],
                        "exclude_patterns": [
                            "node_modules/**",
                            ".git/**",
                            "__pycache__/**",
                        ],
                        "max_file_size_mb": 10,
                        "extract_functions": True,
                        "extract_classes": True,
                        "track_changes": True,
                    },
                },
                "git": {
                    "source_type": "git",
                    "version": "1.0",
                    "batch_mode": "batch",
                    "batch_size": 200,
                    "generate_embeddings": False,
                    "extract_relationships": True,
                    "source_config": {
                        "repository_path": ".",
                        "include_commits": True,
                        "include_branches": True,
                        "include_tags": True,
                        "max_commit_age_days": None,
                        "include_diff_content": True,
                        "max_diff_size_kb": 100,
                    },
                },
            },
            "monitoring": {
                "metrics_retention_hours": 24,
                "max_metrics_per_name": 10000,
                "max_alerts": 1000,
                "enable_system_metrics": True,
                "alert_handlers": [],
            },
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            if output_path.suffix.lower() in [".yaml", ".yml"]:
                yaml.dump(
                    template_config,
                    f,
                    default_flow_style=False,
                    sort_keys=True,
                    indent=2,
                )
            else:
                json.dump(
                    template_config, f, indent=2, sort_keys=True, ensure_ascii=False
                )

        self.logger.info("Template configuration created", output_path=str(output_path))

    # Private methods

    def _load_default_config(self) -> None:
        """Load default configuration."""
        self.config_data = {
            "pipeline": self._default_pipeline_config,
            "adapters": self._default_adapter_configs,
            "monitoring": {
                "metrics_retention_hours": 24,
                "max_metrics_per_name": 10000,
                "max_alerts": 1000,
                "enable_system_metrics": True,
            },
        }

    def _get_default_pipeline_config(self) -> Dict[str, Any]:
        """Get default pipeline configuration."""
        return {
            "max_concurrent_adapters": 10,
            "batch_commit_size": 1000,
            "health_check_interval": 60,
            "metrics_collection_interval": 30,
            "auto_restart_failed_adapters": True,
            "adapter_failure_backoff_seconds": 300,
            "pipeline_shutdown_timeout_seconds": 60,
            "database_url": os.getenv(
                "DATABASE_URL", "postgresql://opsvi@localhost:5432/unified_context"
            ),
            "database_pool_min": 5,
            "database_pool_max": 20,
            "database_command_timeout": 60,
            "max_retry_attempts": 3,
            "retry_base_delay": 1.0,
            "retry_max_delay": 60.0,
            "retry_exponential_base": 2.0,
            "enable_relationship_detection": True,
            "relationship_context_window_size": 100,
            "relationship_batch_size": 50,
            "enable_memory_monitoring": True,
            "max_pipeline_memory_mb": 2048,
            "gc_interval_seconds": 300,
            "enable_duplicate_detection": True,
            "enable_content_validation": True,
            "min_content_length": 1,
            "max_content_length": 1000000,
        }

    def _get_default_adapter_configs(self) -> Dict[str, Any]:
        """Get default adapter configurations."""
        return {}

    def _create_adapter_config(
        self, adapter_id: str, config_dict: Dict[str, Any]
    ) -> AdapterConfig:
        """Create AdapterConfig from dictionary.

        Args:
            adapter_id: Adapter identifier
            config_dict: Configuration dictionary

        Returns:
            AdapterConfig object
        """
        # Map batch mode string to enum
        batch_mode_str = config_dict.get("batch_mode", "streaming")
        try:
            batch_mode = BatchMode(batch_mode_str)
        except ValueError:
            batch_mode = BatchMode.STREAMING
            self.logger.warning(
                "Invalid batch mode, using default",
                adapter_id=adapter_id,
                invalid_mode=batch_mode_str,
            )

        return AdapterConfig(
            adapter_id=adapter_id,
            source_type=config_dict.get("source_type", adapter_id),
            version=config_dict.get("version", "1.0"),
            batch_mode=batch_mode,
            batch_size=config_dict.get("batch_size", 100),
            batch_timeout_seconds=config_dict.get("batch_timeout_seconds", 30),
            max_items_per_second=config_dict.get("max_items_per_second", 1000),
            max_concurrent_batches=config_dict.get("max_concurrent_batches", 5),
            max_retries=config_dict.get("max_retries", 3),
            retry_delay_seconds=config_dict.get("retry_delay_seconds", 1.0),
            retry_backoff_factor=config_dict.get("retry_backoff_factor", 2.0),
            health_check_interval_seconds=config_dict.get(
                "health_check_interval_seconds", 60
            ),
            error_threshold_count=config_dict.get("error_threshold_count", 10),
            error_threshold_window_seconds=config_dict.get(
                "error_threshold_window_seconds", 300
            ),
            strict_validation=config_dict.get("strict_validation", True),
            skip_duplicates=config_dict.get("skip_duplicates", True),
            content_hash_check=config_dict.get("content_hash_check", True),
            generate_embeddings=config_dict.get("generate_embeddings", True),
            generate_summaries=config_dict.get("generate_summaries", False),
            extract_relationships=config_dict.get("extract_relationships", True),
            source_config=config_dict.get("source_config", {}),
            enabled_features=set(config_dict.get("enabled_features", [])),
            disabled_features=set(config_dict.get("disabled_features", [])),
            circuit_breaker_threshold=config_dict.get("circuit_breaker_threshold", 5),
            circuit_breaker_timeout_seconds=config_dict.get(
                "circuit_breaker_timeout_seconds", 60
            ),
            circuit_breaker_reset_threshold=config_dict.get(
                "circuit_breaker_reset_threshold", 3
            ),
            connection_pool_size=config_dict.get("connection_pool_size", 5),
            connection_timeout_seconds=config_dict.get(
                "connection_timeout_seconds", 30
            ),
            max_memory_mb=config_dict.get("max_memory_mb", 512),
            memory_check_interval_seconds=config_dict.get(
                "memory_check_interval_seconds", 30
            ),
        )

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Environment variable mappings
        env_mappings = {
            "UNIFIED_CONTEXT_DATABASE_URL": "pipeline.database_url",
            "UNIFIED_CONTEXT_MAX_CONCURRENT_ADAPTERS": "pipeline.max_concurrent_adapters",
            "UNIFIED_CONTEXT_BATCH_SIZE": "pipeline.batch_commit_size",
            "UNIFIED_CONTEXT_MAX_MEMORY_MB": "pipeline.max_pipeline_memory_mb",
            "UNIFIED_CONTEXT_ENABLE_MONITORING": "pipeline.enable_memory_monitoring",
            "UNIFIED_CONTEXT_LOG_LEVEL": "logging.level",
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Parse the value based on expected type
                if config_path.endswith(
                    ("_size", "_mb", "_count", "_seconds", "_attempts")
                ):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif config_path.endswith(("_rate", "_delay", "_factor")):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                elif value.lower() in ("true", "false"):
                    value = value.lower() == "true"

                # Set the value in config_data
                self._set_nested_config(config_path, value)
                self.logger.debug(
                    "Applied environment override",
                    env_var=env_var,
                    config_path=config_path,
                    value=value,
                )

    def _set_nested_config(self, config_path: str, value: Any) -> None:
        """Set a nested configuration value.

        Args:
            config_path: Dot-separated path (e.g., 'pipeline.database_url')
            value: Value to set
        """
        parts = config_path.split(".")
        current = self.config_data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        errors = []

        # Validate pipeline config
        pipeline_config = self.config_data.get("pipeline", {})
        if "database_url" in pipeline_config:
            if not isinstance(pipeline_config["database_url"], str):
                errors.append("pipeline.database_url must be a string")

        # Validate adapter configs
        adapters_config = self.config_data.get("adapters", {})
        for adapter_id, adapter_config in adapters_config.items():
            if not isinstance(adapter_config, dict):
                errors.append(f"adapters.{adapter_id} must be a dictionary")
                continue

            if "source_type" not in adapter_config:
                errors.append(f"adapters.{adapter_id} missing required 'source_type'")

            batch_mode = adapter_config.get("batch_mode")
            if batch_mode and batch_mode not in [
                "streaming",
                "micro_batch",
                "batch",
                "bulk",
            ]:
                errors.append(
                    f"adapters.{adapter_id}.batch_mode must be one of: "
                    "streaming, micro_batch, batch, bulk"
                )

        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )
