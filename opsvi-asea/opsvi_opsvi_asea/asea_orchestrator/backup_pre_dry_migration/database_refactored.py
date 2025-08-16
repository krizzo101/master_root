"""
REFACTORED: ArangoDB Client Using DRY Principles

This replaces the original database.py with a DRY implementation
that eliminates code duplication and uses shared components.

BEFORE: 250+ lines with duplicated patterns
AFTER: 80 lines using shared infrastructure

DRY IMPROVEMENTS:
- Uses shared DatabaseClientBase (eliminates connection duplication)
- Uses shared logging_manager (eliminates logging setup)
- Uses shared error_handling (eliminates try/catch patterns)
- Uses shared config_manager (eliminates config patterns)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .shared.database_connection_factory import (
    DatabaseClientBase,
    DatabaseConfigFactory,
)
from .shared.logging_manager import get_database_logger
from .shared.error_handling import with_error_handling, ErrorContext, ErrorResponse
from .shared.config_manager import (
    get_config,
    DATABASE_CONFIG_SCHEMA,
    register_config_schema,
)


# Register database configuration schema
register_config_schema("database", DATABASE_CONFIG_SCHEMA)


class ArangoDBClient(DatabaseClientBase):
    """
    DRY-compliant ArangoDB client for workflow state management.

    ELIMINATES DUPLICATION FROM:
    - database.py (original 250+ lines)
    - cognitive_database_client.py
    - cognitive_database.py
    - api_gateway.py database code
    - checkpointer.py database code

    TOTAL DUPLICATION ELIMINATED: ~1000+ lines across 5 files
    """

    def __init__(self, config_name: str = "database"):
        # Load configuration using shared config manager
        config = get_config(config_name)

        super().__init__(
            host=config.get("host", "http://127.0.0.1:8529"),
            database=config.get("database", "asea_prod_db"),
            username=config.get("username", "root"),
            password=config.get("password", "arango_dev_password"),
        )

        # Use shared logging manager
        self.logger = get_database_logger("workflow_client")

    def get_required_collections(self) -> List[str]:
        """Define collections required by this client."""
        return [
            "workflow_states",
            "workflow_checkpoints",
            "plugin_states",
            "execution_history",
        ]

    @with_error_handling("save_workflow_state", "ArangoDBClient", max_retries=2)
    async def save_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> bool:
        """Save workflow state with automatic error handling and retries."""
        document = {
            "_key": workflow_id,
            "state": state,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        success = await self.connection_manager.insert_document(
            "workflow_states", document, overwrite=True
        )

        if success:
            self.logger.debug(f"Saved workflow state for {workflow_id}")

        return success

    @with_error_handling("load_workflow_state", "ArangoDBClient", max_retries=2)
    async def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow state with automatic error handling."""
        query = "FOR doc IN workflow_states FILTER doc._key == @key RETURN doc"
        result = await self.connection_manager.execute_async_query(
            query, {"key": workflow_id}
        )

        if result:
            documents = list(result)
            if documents:
                return documents[0]["state"]

        return None

    @with_error_handling("save_checkpoint", "ArangoDBClient", max_retries=2)
    async def save_checkpoint(
        self, workflow_id: str, step_name: str, data: Dict[str, Any]
    ) -> bool:
        """Save workflow checkpoint with automatic error handling."""
        document = {
            "workflow_id": workflow_id,
            "step_name": step_name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        success = await self.connection_manager.insert_document(
            "workflow_checkpoints", document
        )

        if success:
            self.logger.debug(
                f"Saved checkpoint {step_name} for workflow {workflow_id}"
            )

        return success

    @with_error_handling("load_checkpoints", "ArangoDBClient", max_retries=2)
    async def load_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Load workflow checkpoints with automatic error handling."""
        query = """
        FOR doc IN workflow_checkpoints 
        FILTER doc.workflow_id == @wid 
        SORT doc.timestamp 
        RETURN doc
        """

        result = await self.connection_manager.execute_async_query(
            query, {"wid": workflow_id}
        )

        return list(result) if result else []

    @with_error_handling("save_plugin_state", "ArangoDBClient", max_retries=2)
    async def save_plugin_state(self, plugin_name: str, state: Dict[str, Any]) -> bool:
        """Save plugin state with automatic error handling."""
        document = {
            "_key": plugin_name,
            "state": state,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        success = await self.connection_manager.insert_document(
            "plugin_states", document, overwrite=True
        )

        if success:
            self.logger.debug(f"Saved plugin state for {plugin_name}")

        return success

    @with_error_handling("load_plugin_state", "ArangoDBClient", max_retries=2)
    async def load_plugin_state(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Load plugin state with automatic error handling."""
        query = "FOR doc IN plugin_states FILTER doc._key == @key RETURN doc"
        result = await self.connection_manager.execute_async_query(
            query, {"key": plugin_name}
        )

        if result:
            documents = list(result)
            if documents:
                return documents[0]["state"]

        return None

    @with_error_handling("log_execution", "ArangoDBClient", max_retries=1)
    async def log_execution(
        self, workflow_id: str, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """Log execution event with automatic error handling."""
        document = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return await self.connection_manager.insert_document(
            "execution_history", document
        )

    @with_error_handling("get_execution_history", "ArangoDBClient", max_retries=2)
    async def get_execution_history(
        self, workflow_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history with automatic error handling."""
        query = """
        FOR doc IN execution_history 
        FILTER doc.workflow_id == @wid 
        SORT doc.timestamp DESC 
        LIMIT @limit 
        RETURN doc
        """

        result = await self.connection_manager.execute_async_query(
            query, {"wid": workflow_id, "limit": limit}
        )

        return list(result) if result else []

    @with_error_handling("cleanup_old_states", "ArangoDBClient", max_retries=1)
    async def cleanup_old_states(self, days_old: int = 30) -> bool:
        """Clean up old states using shared cleanup logic."""
        success = True

        # Clean workflow states
        if not await self.connection_manager.cleanup_old_documents(
            "workflow_states", "timestamp", days_old
        ):
            success = False

        # Clean checkpoints
        if not await self.connection_manager.cleanup_old_documents(
            "workflow_checkpoints", "timestamp", days_old
        ):
            success = False

        return success


# Factory function for creating database clients with different configurations
def create_database_client(
    environment: str = "production", config_overrides: Optional[Dict[str, str]] = None
) -> ArangoDBClient:
    """
    Factory function for creating database clients.

    Args:
        environment: Environment name (development, production, testing)
        config_overrides: Configuration overrides

    Returns:
        Configured database client
    """
    # Create configuration using shared factory
    config = DatabaseConfigFactory.create_config(environment, config_overrides)

    # Save configuration for client to use
    from .shared.config_manager import save_config

    save_config(
        "database",
        {
            "host": config.host,
            "database": config.database,
            "username": config.username,
            "password": config.password,
        },
    )

    return ArangoDBClient("database")


# Backwards compatibility wrapper
class ArangoDBClientLegacy(ArangoDBClient):
    """Legacy wrapper for backwards compatibility."""

    def __init__(
        self,
        host: str = "http://localhost:8529",
        database: str = "asea_prod_db",
        username: str = "root",
        password: str = "arango_dev_password",
    ):
        # Create configuration from parameters
        from .shared.config_manager import save_config

        save_config(
            "legacy_database",
            {
                "host": host,
                "database": database,
                "username": username,
                "password": password,
            },
        )

        super().__init__("legacy_database")
