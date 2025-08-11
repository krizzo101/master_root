import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from arango import ArangoClient


logger = logging.getLogger(__name__)


class ArangoDBClient:
    """ArangoDB client for persistent workflow state management using
    python-arango with async support."""

    def __init__(
        self,
        host: str = "http://localhost:8529",
        database: str = "asea_prod_db",
        username: str = "root",
        password: str = "arango_dev_password",
    ):
        self.host = host
        self.database_name = database
        self.username = username
        self.password = password
        self.client = None
        self.db = None
        self.async_db = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to ArangoDB and initialize collections."""
        try:
            # Initialize client
            self.client = ArangoClient(hosts=self.host)

            # Connect to _system database first to create our database if needed
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )

            # Create database if it doesn't exist
            if not sys_db.has_database(self.database_name):
                sys_db.create_database(self.database_name)
                logger.info(f"Created database: {self.database_name}")

            # Connect to our database
            self.db = self.client.db(
                self.database_name, username=self.username, password=self.password
            )

            # Initialize async execution context
            self.async_db = self.db.begin_async_execution(return_result=True)

            # Create collections if they don't exist
            await self._ensure_collections()

            self._connected = True
            logger.info(f"Successfully connected to ArangoDB at {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False

    async def _ensure_collections(self):
        """Ensure required collections exist."""
        collections = [
            "workflow_states",
            "workflow_checkpoints",
            "plugin_states",
            "execution_history",
        ]

        for collection_name in collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")

    async def save_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> bool:
        """Save workflow state with timestamp."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            document = {
                "_key": workflow_id,
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Use async execution
            job = self.async_db.collection("workflow_states").insert(
                document, overwrite=True
            )

            # Wait for completion
            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Saved workflow state for {workflow_id}: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    async def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow state by ID."""
        if not self._connected:
            logger.error("Not connected to database")
            return None

        try:
            # Use async execution for query
            job = self.async_db.aql.execute(
                "FOR doc IN workflow_states FILTER doc._key == @key RETURN doc",
                bind_vars={"key": workflow_id},
            )

            # Wait for completion
            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            documents = list(cursor)

            if documents:
                return documents[0]["state"]
            return None

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    async def save_checkpoint(
        self, workflow_id: str, step_name: str, data: Dict[str, Any]
    ) -> bool:
        """Save a workflow checkpoint."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            document = {
                "workflow_id": workflow_id,
                "step_name": step_name,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            job = self.async_db.collection("workflow_checkpoints").insert(document)

            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Saved checkpoint {step_name} for workflow {workflow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    async def load_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Load all checkpoints for a workflow."""
        if not self._connected:
            logger.error("Not connected to database")
            return []

        try:
            job = self.async_db.aql.execute(
                "FOR doc IN workflow_checkpoints FILTER doc.workflow_id == @wid SORT doc.timestamp RETURN doc",
                bind_vars={"wid": workflow_id},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to load checkpoints: {e}")
            return []

    async def save_plugin_state(self, plugin_name: str, state: Dict[str, Any]) -> bool:
        """Save plugin-specific state."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            document = {
                "_key": plugin_name,
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
            }

            job = self.async_db.collection("plugin_states").insert(
                document, overwrite=True
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Saved plugin state for {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save plugin state: {e}")
            return False

    async def load_plugin_state(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Load plugin-specific state."""
        if not self._connected:
            logger.error("Not connected to database")
            return None

        try:
            job = self.async_db.aql.execute(
                "FOR doc IN plugin_states FILTER doc._key == @key RETURN doc",
                bind_vars={"key": plugin_name},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            documents = list(cursor)

            if documents:
                return documents[0]["state"]
            return None

        except Exception as e:
            logger.error(f"Failed to load plugin state: {e}")
            return None

    async def log_execution(
        self, workflow_id: str, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """Log execution events for audit trail."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            document = {
                "workflow_id": workflow_id,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            job = self.async_db.collection("execution_history").insert(document)

            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            return True

        except Exception as e:
            logger.error(f"Failed to log execution event: {e}")
            return False

    async def get_execution_history(
        self, workflow_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history for a workflow."""
        if not self._connected:
            logger.error("Not connected to database")
            return []

        try:
            job = self.async_db.aql.execute(
                "FOR doc IN execution_history FILTER doc.workflow_id == @wid SORT doc.timestamp DESC LIMIT @limit RETURN doc",
                bind_vars={"wid": workflow_id, "limit": limit},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []

    async def cleanup_old_states(self, days_old: int = 30) -> bool:
        """Clean up old workflow states and checkpoints."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            cutoff_date = (
                datetime.utcnow()
                .replace(day=datetime.utcnow().day - days_old)
                .isoformat()
            )

            # Clean workflow states
            job1 = self.async_db.aql.execute(
                "FOR doc IN workflow_states FILTER doc.timestamp < @cutoff REMOVE doc IN workflow_states",
                bind_vars={"cutoff": cutoff_date},
            )

            # Clean checkpoints
            job2 = self.async_db.aql.execute(
                "FOR doc IN workflow_checkpoints FILTER doc.timestamp < @cutoff REMOVE doc IN workflow_checkpoints",
                bind_vars={"cutoff": cutoff_date},
            )

            while job1.status() != "done" or job2.status() != "done":
                await asyncio.sleep(0.01)

            logger.info(f"Cleaned up states older than {days_old} days")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
            return False

    async def disconnect(self):
        """Clean disconnect from database."""
        if self.async_db:
            # Clear any pending async jobs
            try:
                if hasattr(self.db, "clear_async_jobs"):
                    self.db.clear_async_jobs()
            except:
                pass

        self._connected = False
        logger.info("Disconnected from ArangoDB")

    def __del__(self):
        """Cleanup on destruction."""
        if self._connected:
            # Note: Can't use async in __del__, so just log
            logger.info("ArangoDBClient destroyed - connection may still be open")
