"""
DRY Plugin Execution Base - Eliminates Plugin Pattern Duplication

This module provides base classes and decorators to eliminate the massive
duplication found in 20+ plugin execute() methods.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Union, List
from functools import wraps
from datetime import datetime
from abc import ABC, abstractmethod

from ..plugins.types import (
    ExecutionContext,
    PluginResult,
    PluginConfig,
    ValidationResult,
)


logger = logging.getLogger(__name__)


def execution_wrapper(
    validate_input: bool = True,
    require_params: Optional[List[str]] = None,
    default_action: str = "execute",
    log_execution: bool = True,
):
    """
    Decorator to eliminate common execution boilerplate in plugins.

    Eliminates duplication of:
    - Input validation
    - Parameter extraction
    - Error handling
    - Logging
    - Result formatting

    Args:
        validate_input: Whether to validate input parameters
        require_params: List of required parameters
        default_action: Default action if none specified
        log_execution: Whether to log execution details
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, context: ExecutionContext) -> PluginResult:
            plugin_name = getattr(self, "get_name", lambda: self.__class__.__name__)()
            start_time = datetime.utcnow()

            try:
                # Log execution start
                if log_execution:
                    logger.info(f"Executing plugin: {plugin_name}")

                # Validate required parameters
                if require_params:
                    missing_params = [
                        p for p in require_params if p not in context.state
                    ]
                    if missing_params:
                        return PluginResult(
                            success=False,
                            error_message=f"Missing required parameters: {missing_params}",
                        )

                # Validate input if requested
                if validate_input and hasattr(self, "validate_input"):
                    validation = self.validate_input(context.state)
                    if not validation.is_valid:
                        return PluginResult(
                            success=False,
                            error_message=f"Input validation failed: {validation.errors}",
                        )

                # Execute the actual plugin logic
                result = await func(self, context)

                # Add execution metadata
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                if result.success and log_execution:
                    logger.info(
                        f"Plugin {plugin_name} executed successfully in {execution_time:.3f}s"
                    )
                elif not result.success:
                    logger.error(f"Plugin {plugin_name} failed: {result.error_message}")

                # Add metadata to result
                if result.data is None:
                    result.data = {}

                result.data.update(
                    {
                        "execution_time": execution_time,
                        "plugin_name": plugin_name,
                        "timestamp": start_time.isoformat() + "Z",
                    }
                )

                return result

            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Plugin {plugin_name} crashed after {execution_time:.3f}s: {e}",
                    exc_info=True,
                )

                return PluginResult(
                    success=False,
                    error_message=f"Plugin execution failed: {str(e)}",
                    data={
                        "execution_time": execution_time,
                        "plugin_name": plugin_name,
                        "timestamp": start_time.isoformat() + "Z",
                        "exception_type": type(e).__name__,
                    },
                )

        return wrapper

    return decorator


class StandardPluginBase(ABC):
    """
    Base class eliminating common plugin patterns and boilerplate.

    Eliminates duplication across 20+ plugins of:
    - Initialization patterns
    - Configuration handling
    - Error handling
    - Cleanup logic
    - State management
    """

    def __init__(self):
        self.config: Optional[PluginConfig] = None
        self._initialized = False
        self._execution_count = 0
        self._last_execution: Optional[datetime] = None

    async def initialize(self, config: PluginConfig, event_bus=None) -> None:
        """Standard initialization pattern."""
        try:
            self.config = config
            await self._custom_initialization(config, event_bus)
            self._initialized = True
            logger.info(f"Plugin {self.get_name()} initialized successfully")
        except Exception as e:
            logger.error(f"Plugin {self.get_name()} initialization failed: {e}")
            raise

    @abstractmethod
    async def _custom_initialization(
        self, config: PluginConfig, event_bus=None
    ) -> None:
        """Override this for plugin-specific initialization."""
        pass

    @execution_wrapper(validate_input=True, log_execution=True)
    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Standard execution pattern with automatic wrapping."""
        self._execution_count += 1
        self._last_execution = datetime.utcnow()

        # Delegate to plugin-specific implementation
        return await self._execute_impl(context)

    @abstractmethod
    async def _execute_impl(self, context: ExecutionContext) -> PluginResult:
        """Override this for plugin-specific execution logic."""
        pass

    async def cleanup(self) -> None:
        """Standard cleanup pattern."""
        try:
            await self._custom_cleanup()
            logger.info(f"Plugin {self.get_name()} cleaned up successfully")
        except Exception as e:
            logger.error(f"Plugin {self.get_name()} cleanup failed: {e}")

    async def _custom_cleanup(self) -> None:
        """Override this for plugin-specific cleanup."""
        pass

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return plugin name."""
        pass

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Default input validation - override if needed."""
        return ValidationResult(is_valid=True, errors=[])

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "execution_count": self._execution_count,
            "last_execution": self._last_execution.isoformat() + "Z"
            if self._last_execution
            else None,
            "initialized": self._initialized,
            "plugin_name": self.get_name(),
        }


class ActionBasedPluginBase(StandardPluginBase):
    """
    Base class for plugins that handle multiple actions.

    Eliminates the action dispatch pattern found in multiple plugins.
    """

    @execution_wrapper(
        validate_input=True, log_execution=True, default_action="default"
    )
    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Standard action-based execution."""
        self._execution_count += 1
        self._last_execution = datetime.utcnow()

        action = context.state.get("action", "default")

        # Look for action handler method
        handler_name = f"_handle_{action}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(context)
        else:
            available_actions = [
                method[8:]
                for method in dir(self)
                if method.startswith("_handle_") and callable(getattr(self, method))
            ]
            return PluginResult(
                success=False,
                error_message=f"Unknown action: {action}. Available actions: {available_actions}",
            )

    @abstractmethod
    async def _handle_default(self, context: ExecutionContext) -> PluginResult:
        """Default action handler."""
        pass


class ConfigurablePluginMixin:
    """
    Mixin providing standard configuration handling patterns.

    Eliminates configuration boilerplate across plugins.
    """

    def get_config_value(
        self, key: str, default: Any = None, required: bool = False
    ) -> Any:
        """Get configuration value with validation."""
        if not hasattr(self, "config") or self.config is None:
            if required:
                raise ValueError(
                    f"Configuration not initialized, cannot get required key: {key}"
                )
            return default

        value = self.config.config.get(key, default)

        if required and value is None:
            raise ValueError(f"Required configuration key missing: {key}")

        return value

    def validate_config_schema(self, schema: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema."""
        if not hasattr(self, "config") or self.config is None:
            return ValidationResult(
                is_valid=False, errors=["Configuration not initialized"]
            )

        errors = []

        for key, requirements in schema.items():
            required = requirements.get("required", False)
            value_type = requirements.get("type")
            default = requirements.get("default")

            value = self.config.config.get(key, default)

            if required and value is None:
                errors.append(f"Required configuration key missing: {key}")

            if value is not None and value_type is not None:
                if not isinstance(value, value_type):
                    errors.append(
                        f"Configuration key {key} must be of type {value_type.__name__}"
                    )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class DatabasePluginMixin:
    """
    Mixin providing standard database operations for plugins.

    Eliminates database handling duplication.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db_connection = None

    async def init_database_connection(self):
        """Initialize database connection using shared factory."""
        from .database_connection_factory import (
            DatabaseConfigFactory,
            ArangoConnectionManager,
        )

        # Get database config from plugin config or use defaults
        db_config = self.get_config_value("database", {})
        environment = db_config.get("environment", "production")

        config = DatabaseConfigFactory.create_config(
            environment, db_config.get("overrides")
        )
        self._db_connection = ArangoConnectionManager(config)

        return await self._db_connection.connect()

    async def save_plugin_state(self, state: Dict[str, Any]) -> bool:
        """Save plugin state to database."""
        if not self._db_connection or not self._db_connection.is_connected:
            logger.warning("Database not connected, cannot save plugin state")
            return False

        document = {
            "_key": f"plugin_state_{self.get_name()}",
            "plugin_name": self.get_name(),
            "state": state,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return await self._db_connection.insert_document(
            "plugin_states", document, overwrite=True
        )

    async def load_plugin_state(self) -> Optional[Dict[str, Any]]:
        """Load plugin state from database."""
        if not self._db_connection or not self._db_connection.is_connected:
            logger.warning("Database not connected, cannot load plugin state")
            return None

        query = """
        FOR doc IN plugin_states
        FILTER doc._key == @key
        RETURN doc.state
        """

        result = await self._db_connection.execute_async_query(
            query, {"key": f"plugin_state_{self.get_name()}"}
        )

        if result and len(list(result)) > 0:
            return list(result)[0]

        return None


# Factory for creating standardized plugins
class PluginFactory:
    """Factory for creating plugins with standardized patterns."""

    @staticmethod
    def create_simple_plugin(
        name: str,
        execute_func: Callable[[ExecutionContext], PluginResult],
        capabilities: Optional[List[str]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
    ) -> type:
        """
        Create a simple plugin class from a function.

        Eliminates boilerplate for simple plugins.
        """

        class GeneratedPlugin(StandardPluginBase):
            @classmethod
            def get_name(cls) -> str:
                return name

            async def _custom_initialization(
                self, config: PluginConfig, event_bus=None
            ) -> None:
                pass

            async def _execute_impl(self, context: ExecutionContext) -> PluginResult:
                if asyncio.iscoroutinefunction(execute_func):
                    return await execute_func(context)
                else:
                    return execute_func(context)

            def get_capabilities(self) -> List[str]:
                return capabilities or [name]

            @staticmethod
            def get_configuration_schema() -> Dict[str, Any]:
                return config_schema or {}

        return GeneratedPlugin


# Common validation utilities
class ValidationUtils:
    """Common validation patterns used across plugins."""

    @staticmethod
    def validate_required_params(
        context: ExecutionContext, required: List[str]
    ) -> ValidationResult:
        """Validate required parameters are present."""
        missing = [param for param in required if param not in context.state]

        if missing:
            return ValidationResult(
                is_valid=False, errors=[f"Missing required parameters: {missing}"]
            )

        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def validate_param_types(
        context: ExecutionContext, type_map: Dict[str, type]
    ) -> ValidationResult:
        """Validate parameter types."""
        errors = []

        for param, expected_type in type_map.items():
            if param in context.state:
                value = context.state[param]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Parameter {param} must be of type {expected_type.__name__}, got {type(value).__name__}"
                    )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @staticmethod
    def validate_choice_param(
        context: ExecutionContext, param: str, choices: List[Any]
    ) -> ValidationResult:
        """Validate parameter is one of allowed choices."""
        if param in context.state:
            value = context.state[param]
            if value not in choices:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Parameter {param} must be one of {choices}, got {value}"],
                )

        return ValidationResult(is_valid=True, errors=[])
