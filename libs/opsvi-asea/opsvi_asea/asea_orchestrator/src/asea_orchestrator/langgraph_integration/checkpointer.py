"""
ASEA ArangoDB Checkpointer for LangGraph Integration

Provides persistent checkpointing using ArangoDB to maintain workflow state
across executions and enable resumption capabilities.
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
)
from ..shared.database_connection_factory import (
    DatabaseConfigFactory,
    ArangoConnectionManager,
)


class ASEAArangoCheckpointer(BaseCheckpointSaver):
    """
    ArangoDB-based checkpointer for LangGraph workflows.

    This checkpointer stores workflow state in ArangoDB, enabling:
    - Persistent workflow state across restarts
    - Workflow resumption from any checkpoint
    - State history and time travel
    - Integration with existing ASEA ArangoDB infrastructure
    """

    def __init__(
        self,
        host: str = "http://127.0.0.1:8529",
        username: str = "root",
        password: str = "arango_dev_password",
        database: str = "asea_development",
        collection: str = "langgraph_checkpoints",
    ):
        """
        Initialize the ArangoDB checkpointer.

        Args:
            host: ArangoDB host URL
            username: Database username
            password: Database password
            database: Database name
            collection: Collection name for storing checkpoints
        """
        super().__init__()

        self.client = ArangoConnectionManager(
            DatabaseConfigFactory.create_config("production")
        )
        self.db = self.client.db(database, username=username, password=password)
        self.collection_name = collection

        # Ensure collection exists
        if not self.db.has_collection(collection):
            self.db.create_collection(collection)

        self.collection = self.db.collection(collection)

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> None:
        """
        Store a checkpoint in ArangoDB.

        Args:
            config: Configuration for the checkpoint
            checkpoint: The checkpoint data to store
            metadata: Metadata about the checkpoint
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id is required in config")

        checkpoint_doc = {
            "_key": f"{thread_id}_{checkpoint.ts}",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint.id,
            "timestamp": checkpoint.ts,
            "channel_values": self._serialize_values(checkpoint.channel_values),
            "channel_versions": checkpoint.channel_versions,
            "versions_seen": checkpoint.versions_seen,
            "metadata": {
                "source": metadata.source,
                "step": metadata.step,
                "writes": metadata.writes,
                "parents": metadata.parents,
            },
            "created_at": datetime.now().isoformat(),
            "workflow_name": config.get("workflow_name"),
            "run_id": config.get("run_id"),
        }

        try:
            self.collection.insert(checkpoint_doc, overwrite=True)
        except Exception as e:
            print(f"Error storing checkpoint: {e}")
            raise

    def get_tuple(
        self, config: Dict[str, Any]
    ) -> Optional[Tuple[Checkpoint, CheckpointMetadata]]:
        """
        Retrieve the latest checkpoint for a thread.

        Args:
            config: Configuration containing thread_id

        Returns:
            Tuple of (Checkpoint, CheckpointMetadata) or None if not found
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None

        try:
            # Get the latest checkpoint for this thread
            query = """
            FOR doc IN @@collection
            FILTER doc.thread_id == @thread_id
            SORT doc.timestamp DESC
            LIMIT 1
            RETURN doc
            """

            cursor = self.db.aql.execute(
                query,
                bind_vars={"@collection": self.collection_name, "thread_id": thread_id},
            )

            docs = list(cursor)
            if not docs:
                return None

            doc = docs[0]

            # Reconstruct checkpoint
            checkpoint = Checkpoint(
                v=1,  # Version
                id=doc["checkpoint_id"],
                ts=doc["timestamp"],
                channel_values=self._deserialize_values(doc["channel_values"]),
                channel_versions=doc["channel_versions"],
                versions_seen=doc["versions_seen"],
            )

            # Reconstruct metadata
            metadata = CheckpointMetadata(
                source=doc["metadata"]["source"],
                step=doc["metadata"]["step"],
                writes=doc["metadata"]["writes"],
                parents=doc["metadata"]["parents"],
            )

            return (checkpoint, metadata)

        except Exception as e:
            print(f"Error retrieving checkpoint: {e}")
            return None

    def list(
        self,
        config: Dict[str, Any],
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Tuple[Checkpoint, CheckpointMetadata]]:
        """
        List checkpoints for a thread.

        Args:
            config: Configuration containing thread_id
            filter: Optional filter criteria
            before: Optional timestamp to filter before
            limit: Optional limit on number of results

        Returns:
            List of (Checkpoint, CheckpointMetadata) tuples
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return []

        try:
            query_parts = [
                "FOR doc IN @@collection",
                "FILTER doc.thread_id == @thread_id",
            ]

            bind_vars = {"@collection": self.collection_name, "thread_id": thread_id}

            if before:
                query_parts.append("FILTER doc.timestamp < @before")
                bind_vars["before"] = before

            query_parts.append("SORT doc.timestamp DESC")

            if limit:
                query_parts.append("LIMIT @limit")
                bind_vars["limit"] = limit

            query_parts.append("RETURN doc")

            query = "\n".join(query_parts)

            cursor = self.db.aql.execute(query, bind_vars=bind_vars)

            results = []
            for doc in cursor:
                checkpoint = Checkpoint(
                    v=1,
                    id=doc["checkpoint_id"],
                    ts=doc["timestamp"],
                    channel_values=self._deserialize_values(doc["channel_values"]),
                    channel_versions=doc["channel_versions"],
                    versions_seen=doc["versions_seen"],
                )

                metadata = CheckpointMetadata(
                    source=doc["metadata"]["source"],
                    step=doc["metadata"]["step"],
                    writes=doc["metadata"]["writes"],
                    parents=doc["metadata"]["parents"],
                )

                results.append((checkpoint, metadata))

            return results

        except Exception as e:
            print(f"Error listing checkpoints: {e}")
            return []

    def _serialize_values(self, values: Dict[str, Any]) -> Dict[str, str]:
        """
        Serialize channel values for storage in ArangoDB.

        Args:
            values: Channel values to serialize

        Returns:
            Serialized values as JSON strings
        """
        return {k: json.dumps(v, default=str) for k, v in values.items()}

    def _deserialize_values(self, serialized: Dict[str, str]) -> Dict[str, Any]:
        """
        Deserialize channel values from ArangoDB storage.

        Args:
            serialized: Serialized values from database

        Returns:
            Deserialized values
        """
        return {k: json.loads(v) for k, v in serialized.items()}

    def get_workflow_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get complete workflow execution history for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of workflow state snapshots
        """
        try:
            query = """
            FOR doc IN @@collection
            FILTER doc.thread_id == @thread_id
            SORT doc.timestamp ASC
            RETURN {
                timestamp: doc.timestamp,
                step: doc.metadata.step,
                workflow_state: doc.channel_values,
                created_at: doc.created_at
            }
            """

            cursor = self.db.aql.execute(
                query,
                bind_vars={"@collection": self.collection_name, "thread_id": thread_id},
            )

            return list(cursor)

        except Exception as e:
            print(f"Error retrieving workflow history: {e}")
            return []
