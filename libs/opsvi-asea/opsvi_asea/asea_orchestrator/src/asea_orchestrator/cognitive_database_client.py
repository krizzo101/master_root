"""
MIGRATED TO DRY ARCHITECTURE - 2025-06-24

This file has been migrated to use shared DRY infrastructure.
Original file backed up to: backup_pre_dry_migration/

DRY IMPROVEMENTS:
- Database connection logic moved to shared/database_connection_factory.py
- Error handling moved to shared/error_handling.py  
- Logging moved to shared/logging_manager.py

For new implementation, see: database_refactored.py
"""

# DEPRECATED: This file is kept for backwards compatibility
# Use database_refactored.py for new implementations

import asyncio
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

from arango import ArangoClient


from .shared.logging_manager import get_logger

logger = get_logger(__name__)


class CognitiveArangoDBClient:
    """ArangoDB client using cognitive architecture for workflow state management.

    Replaces legacy workflow collections with cognitive concepts and agent memory
    following the cognitive database interface guide patterns.
    """

    def __init__(
        self,
        host: str = "http://127.0.0.1:8531",
        database: str = "asea_prod_db",
        username: str = "root",
        password: str = "arango_production_password",
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
        """Connect to ArangoDB and validate cognitive collections exist."""
        try:
            # Initialize client
            self.client = ArangoClient(hosts=self.host)

            # Connect to our database (should already exist)
            self.db = self.client.db(
                self.database_name, username=self.username, password=self.password
            )

            # Initialize async execution context
            self.async_db = self.db.begin_async_execution(return_result=True)

            # Validate cognitive collections exist
            await self._validate_cognitive_collections()

            self._connected = True
            logger.info(
                f"Successfully connected to ArangoDB cognitive architecture at {self.host}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False

    async def _validate_cognitive_collections(self):
        """Validate that primary cognitive collections exist."""
        required_collections = [
            "agent_memory",
            "cognitive_concepts",
            "memory_relationships",
            "semantic_relationships",
            "session_context",
            "memory_validation_rules",
            "memory_quality_metrics",
        ]

        for collection_name in required_collections:
            if not self.db.has_collection(collection_name):
                logger.warning(f"Cognitive collection missing: {collection_name}")
            else:
                logger.debug(f"Validated cognitive collection: {collection_name}")

    def _generate_concept_id(self, domain: str, concept_type: str, content: str) -> str:
        """Generate consistent concept ID for cognitive concepts."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{domain}_{concept_type}_{content_hash}"

    async def save_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> bool:
        """Save workflow state as cognitive concept with quality filtering."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            # Extract quality metrics for filtering
            quality_score = state.get("quality_score", 0)
            status = state.get("status", "UNKNOWN")

            # Only store high-quality completed workflows as cognitive concepts
            if status == "COMPLETED" and quality_score >= 7:
                concept_id = self._generate_concept_id(
                    "operational", "workflow_execution", workflow_id
                )

                # Extract success patterns and insights
                success_patterns = []
                if "reasoning" in state:
                    success_patterns.append("ai_reasoning_effective")
                if "critique" in state and state.get("critique_score", 0) > 7:
                    success_patterns.append("critique_improved_output")
                if "improvement" in state:
                    success_patterns.append("iterative_improvement_applied")

                concept_document = {
                    "_key": concept_id,
                    "concept_id": concept_id,
                    "semantic_embedding": None,
                    "knowledge_domain": "operational",
                    "concept_type": "workflow_execution",
                    "abstraction_level": "operational",
                    "confidence_score": min(quality_score / 10.0, 1.0),
                    "evidence_strength": "high" if quality_score >= 8 else "medium",
                    "learning_context": {
                        "workflow_id": workflow_id,
                        "execution_time": state.get("execution_time"),
                        "validation_method": "quality_score_filtering",
                    },
                    "knowledge_content": {
                        "title": f"Successful {state.get('workflow_name', 'workflow')} execution",
                        "workflow_name": state.get("workflow_name"),
                        "quality_score": quality_score,
                        "execution_time": state.get("execution_time"),
                        "success_patterns": success_patterns,
                        "key_insights": self._extract_workflow_insights(state),
                    },
                    "created": datetime.utcnow().isoformat() + "Z",
                    "last_validated": datetime.utcnow().isoformat() + "Z",
                }

                job = self.async_db.collection("cognitive_concepts").insert(
                    concept_document, overwrite=True
                )

                while job.status() != "done":
                    await asyncio.sleep(0.01)

                result = job.result()
                logger.info(
                    f"Stored high-quality workflow as cognitive concept: {concept_id}"
                )
                return True

            # Store operational state as agent memory for resumption capability
            memory_document = {
                "title": f"Workflow State: {workflow_id}",
                "content": f"Workflow {state.get('workflow_name')} state for resumption",
                "tags": [
                    "workflow_state",
                    "operational",
                    state.get("workflow_name", "unknown"),
                ],
                "tier": "operational",
                "memory_type": "operational",
                "validation_status": "system_generated",
                "workflow_data": state,
                "created": datetime.utcnow().isoformat() + "Z",
            }

            job = self.async_db.collection("agent_memory").insert(
                memory_document, overwrite=True
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Saved workflow state as agent memory: {workflow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    def _extract_workflow_insights(self, state: Dict[str, Any]) -> List[str]:
        """Extract key insights from successful workflow execution."""
        insights = []

        if state.get("quality_score", 0) >= 8:
            insights.append("High-quality output achieved")

        if state.get("execution_time", 0) < 30:
            insights.append("Fast execution time")
        elif state.get("execution_time", 0) > 60:
            insights.append("Complex processing required extended time")

        if "model_usage" in state:
            insights.append(f"Effective model usage pattern: {state['model_usage']}")

        if state.get("budget_analysis", {}).get("cost_efficiency") == "high":
            insights.append("Cost-efficient execution")

        return insights

    async def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow state from agent memory or reconstruct from cognitive concepts."""
        if not self._connected:
            logger.error("Not connected to database")
            return None

        try:
            # First try to load from agent memory (operational/failed workflows)
            job = self.async_db.aql.execute(
                """
                FOR memory IN agent_memory
                FILTER CONTAINS(memory.tags, "workflow_state")
                AND memory.workflow_data != null
                AND memory.workflow_data.run_id == @workflow_id
                SORT memory.created DESC
                LIMIT 1
                RETURN memory
                """,
                bind_vars={"workflow_id": workflow_id},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            documents = list(cursor)

            if documents:
                return documents[0]["workflow_data"]

            # If not found in agent memory, try to reconstruct from cognitive concepts
            # (for high-quality completed workflows)
            job = self.async_db.aql.execute(
                """
                FOR concept IN cognitive_concepts
                FILTER concept.concept_type == "workflow_execution"
                AND concept.learning_context.workflow_id == @workflow_id
                SORT concept.created DESC
                LIMIT 1
                RETURN concept
                """,
                bind_vars={"workflow_id": workflow_id},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            documents = list(cursor)

            if documents:
                concept = documents[0]
                # Reconstruct workflow state from cognitive concept
                content = concept.get("knowledge_content", {})
                return {
                    "run_id": workflow_id,
                    "workflow_name": content.get("workflow_name", "unknown"),
                    "status": "COMPLETED",  # Cognitive concepts are only created for completed workflows
                    "current_step": 999,  # Indicate completion
                    "quality_score": content.get("quality_score", 0),
                    "execution_time": content.get("execution_time", 0),
                    "state": {
                        "success_patterns": content.get("success_patterns", []),
                        "key_insights": content.get("key_insights", []),
                        "quality_score": content.get("quality_score", 0),
                    },
                }

            return None

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    async def save_checkpoint(
        self, workflow_id: str, step_name: str, data: Dict[str, Any]
    ) -> bool:
        """Save workflow checkpoint as cognitive concept if valuable."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            # Only store checkpoints that contain valuable insights
            if self._is_valuable_checkpoint(data):
                concept_id = self._generate_concept_id(
                    "operational", "workflow_checkpoint", f"{workflow_id}_{step_name}"
                )

                concept_document = {
                    "_key": concept_id,
                    "concept_id": concept_id,
                    "knowledge_domain": "operational",
                    "concept_type": "workflow_checkpoint",
                    "abstraction_level": "tactical",
                    "confidence_score": 0.8,
                    "evidence_strength": "medium",
                    "learning_context": {
                        "workflow_id": workflow_id,
                        "step_name": step_name,
                        "validation_method": "checkpoint_analysis",
                    },
                    "knowledge_content": {
                        "title": f"Checkpoint: {step_name}",
                        "step_name": step_name,
                        "workflow_id": workflow_id,
                        "checkpoint_data": data,
                        "insights": self._extract_checkpoint_insights(data),
                    },
                    "created": datetime.utcnow().isoformat() + "Z",
                }

                job = self.async_db.collection("cognitive_concepts").insert(
                    concept_document
                )

                while job.status() != "done":
                    await asyncio.sleep(0.01)

                logger.debug(
                    f"Saved valuable checkpoint as cognitive concept: {step_name}"
                )
                return True
            else:
                # Store as temporary agent memory for operational purposes
                memory_document = {
                    "title": f"Checkpoint: {step_name}",
                    "content": f"Workflow checkpoint for step {step_name}",
                    "tags": ["checkpoint", "temporary", workflow_id],
                    "tier": "temporary",
                    "memory_type": "operational",
                    "checkpoint_data": data,
                    "created": datetime.utcnow().isoformat() + "Z",
                }

                job = self.async_db.collection("agent_memory").insert(memory_document)

                while job.status() != "done":
                    await asyncio.sleep(0.01)

                logger.debug(f"Saved checkpoint as temporary memory: {step_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def _is_valuable_checkpoint(self, data: Dict[str, Any]) -> bool:
        """Determine if checkpoint contains valuable insights worth storing as cognitive concept."""
        # Check for quality indicators
        if data.get("quality_score", 0) >= 7:
            return True
        if data.get("optimization_found", False):
            return True
        if data.get("error_prevented", False):
            return True
        if "successful_pattern" in data:
            return True
        return False

    def _extract_checkpoint_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract insights from checkpoint data."""
        insights = []

        if data.get("optimization_found"):
            insights.append("Optimization opportunity identified")
        if data.get("error_prevented"):
            insights.append("Error prevention successful")
        if data.get("quality_score", 0) >= 8:
            insights.append("High-quality intermediate result")

        return insights

    async def load_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Load checkpoints from agent memory and cognitive concepts."""
        if not self._connected:
            logger.error("Not connected to database")
            return []

        try:
            # Load from both agent memory and cognitive concepts
            job = self.async_db.aql.execute(
                """
                LET memory_checkpoints = (
                    FOR memory IN agent_memory
                    FILTER CONTAINS(memory.tags, "checkpoint")
                    AND CONTAINS(memory.tags, @workflow_id)
                    RETURN {
                        source: "agent_memory",
                        data: memory.checkpoint_data,
                        created: memory.created
                    }
                )
                LET concept_checkpoints = (
                    FOR concept IN cognitive_concepts
                    FILTER concept.concept_type == "workflow_checkpoint"
                    AND concept.learning_context.workflow_id == @workflow_id
                    RETURN {
                        source: "cognitive_concepts",
                        data: concept.knowledge_content.checkpoint_data,
                        created: concept.created
                    }
                )
                FOR checkpoint IN UNION(memory_checkpoints, concept_checkpoints)
                SORT checkpoint.created ASC
                RETURN checkpoint
                """,
                bind_vars={"workflow_id": workflow_id},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to load checkpoints: {e}")
            return []

    async def save_plugin_state(self, plugin_name: str, state: Dict[str, Any]) -> bool:
        """Save plugin state as agent memory with procedural type."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            memory_document = {
                "_key": f"plugin_state_{plugin_name}",
                "title": f"Plugin State: {plugin_name}",
                "content": f"Current state and configuration for {plugin_name} plugin",
                "tags": ["plugin_state", "procedural", plugin_name],
                "tier": "operational",
                "memory_type": "procedural",
                "validation_status": "system_generated",
                "plugin_data": state,
                "created": datetime.utcnow().isoformat() + "Z",
            }

            job = self.async_db.collection("agent_memory").insert(
                memory_document, overwrite=True
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Saved plugin state as agent memory: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save plugin state: {e}")
            return False

    async def load_plugin_state(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Load plugin state from agent memory."""
        if not self._connected:
            logger.error("Not connected to database")
            return None

        try:
            job = self.async_db.aql.execute(
                """
                FOR memory IN agent_memory
                FILTER memory._key == @key
                SORT memory.created DESC
                LIMIT 1
                RETURN memory
                """,
                bind_vars={"key": f"plugin_state_{plugin_name}"},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            documents = list(cursor)

            if documents:
                return documents[0]["plugin_data"]
            return None

        except Exception as e:
            logger.error(f"Failed to load plugin state: {e}")
            return None

    async def log_execution(
        self, workflow_id: str, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """Log significant execution events as cognitive concepts."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            # Only log significant events as cognitive concepts
            if self._is_significant_event(event_type, data):
                concept_id = self._generate_concept_id(
                    "operational", "execution_pattern", f"{workflow_id}_{event_type}"
                )

                concept_document = {
                    "_key": concept_id,
                    "concept_id": concept_id,
                    "knowledge_domain": "operational",
                    "concept_type": "execution_pattern",
                    "abstraction_level": "tactical",
                    "confidence_score": 0.7,
                    "evidence_strength": "medium",
                    "learning_context": {
                        "workflow_id": workflow_id,
                        "event_type": event_type,
                        "validation_method": "execution_analysis",
                    },
                    "knowledge_content": {
                        "title": f"Execution Pattern: {event_type}",
                        "event_type": event_type,
                        "workflow_id": workflow_id,
                        "execution_data": data,
                        "pattern_insights": self._extract_execution_insights(
                            event_type, data
                        ),
                    },
                    "created": datetime.utcnow().isoformat() + "Z",
                }

                job = self.async_db.collection("cognitive_concepts").insert(
                    concept_document
                )

                while job.status() != "done":
                    await asyncio.sleep(0.01)

                logger.debug(
                    f"Logged significant execution event as cognitive concept: {event_type}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to log execution event: {e}")
            return False

    def _is_significant_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Determine if execution event is significant enough to store as cognitive concept."""
        significant_events = [
            "workflow_completed_successfully",
            "optimization_discovered",
            "error_pattern_identified",
            "performance_improvement",
            "quality_threshold_exceeded",
        ]

        if event_type in significant_events:
            return True
        if data.get("quality_score", 0) >= 8:
            return True
        if data.get("performance_improvement", 0) > 0.2:
            return True

        return False

    def _extract_execution_insights(
        self, event_type: str, data: Dict[str, Any]
    ) -> List[str]:
        """Extract insights from execution events."""
        insights = []

        if event_type == "workflow_completed_successfully":
            insights.append("Successful workflow completion pattern")
        if data.get("optimization_discovered"):
            insights.append("Optimization opportunity pattern identified")
        if data.get("error_prevented"):
            insights.append("Error prevention pattern effective")

        return insights

    async def get_execution_history(
        self, workflow_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history from cognitive concepts."""
        if not self._connected:
            logger.error("Not connected to database")
            return []

        try:
            job = self.async_db.aql.execute(
                """
                FOR concept IN cognitive_concepts
                FILTER concept.concept_type == "execution_pattern"
                AND concept.learning_context.workflow_id == @workflow_id
                SORT concept.created DESC
                LIMIT @limit
                RETURN concept
                """,
                bind_vars={"workflow_id": workflow_id, "limit": limit},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []

    async def cleanup_temporary_data(self, days_old: int = 1) -> bool:
        """Clean up temporary agent memories (not cognitive concepts)."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            cutoff_date = (
                datetime.utcnow()
                .replace(day=datetime.utcnow().day - days_old)
                .isoformat()
            )

            # Only clean temporary memories, preserve cognitive concepts
            job = self.async_db.aql.execute(
                """
                FOR memory IN agent_memory
                FILTER memory.tier == "temporary"
                AND memory.created < @cutoff
                REMOVE memory IN agent_memory
                """,
                bind_vars={"cutoff": cutoff_date},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            logger.info(f"Cleaned up temporary memories older than {days_old} days")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup temporary data: {e}")
            return False

    async def get_workflow_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get successful workflow patterns for learning."""
        if not self._connected:
            logger.error("Not connected to database")
            return []

        try:
            job = self.async_db.aql.execute(
                """
                FOR concept IN cognitive_concepts
                FILTER concept.concept_type == "workflow_execution"
                AND concept.confidence_score > 0.7
                SORT concept.confidence_score DESC, concept.created DESC
                LIMIT @limit
                RETURN concept
                """,
                bind_vars={"limit": limit},
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            cursor = job.result()
            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to get workflow patterns: {e}")
            return []

    async def create_semantic_relationship(
        self,
        from_concept_id: str,
        to_concept_id: str,
        relationship_type: str,
        strength: float = 0.8,
    ) -> bool:
        """Create semantic relationship between cognitive concepts."""
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            relationship_document = {
                "_from": f"cognitive_concepts/{from_concept_id}",
                "_to": f"cognitive_concepts/{to_concept_id}",
                "relationship_type": relationship_type,
                "semantic_similarity": strength,
                "relationship_strength": "high"
                if strength > 0.8
                else "medium"
                if strength > 0.6
                else "low",
                "discovery_method": "workflow_analysis",
                "compound_learning_potential": strength,
                "evidence": [
                    "workflow_execution_patterns",
                    "quality_score_correlation",
                ],
                "created": datetime.utcnow().isoformat() + "Z",
            }

            job = self.async_db.collection("semantic_relationships").insert(
                relationship_document
            )

            while job.status() != "done":
                await asyncio.sleep(0.01)

            logger.debug(
                f"Created semantic relationship: {from_concept_id} -> {to_concept_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create semantic relationship: {e}")
            return False

    async def disconnect(self):
        """Clean disconnect from database."""
        if self.async_db:
            try:
                if hasattr(self.db, "clear_async_jobs"):
                    self.db.clear_async_jobs()
            except:
                pass

        self._connected = False
        logger.info("Disconnected from ArangoDB cognitive architecture")

    def __del__(self):
        """Cleanup on destruction."""
        if self._connected:
            logger.info(
                "CognitiveArangoDBClient destroyed - connection may still be open"
            )


# DRY MIGRATION: Redirect to new implementation
try:
    from .database_refactored import ArangoDBClient as _NewArangoDBClient
    from .shared.logging_manager import get_logger

    _logger = get_logger(__name__)
    _logger.warning(
        f"DEPRECATED: {__file__} is deprecated. "
        "Use database_refactored.py for new implementations."
    )

    # Provide backwards compatibility
    ArangoDBClient = _NewArangoDBClient

except ImportError:
    # Fallback to original implementation if new one not available
    pass
