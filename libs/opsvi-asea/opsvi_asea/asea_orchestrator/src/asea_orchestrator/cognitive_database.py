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

"""
Cognitive Database Interface for Quality-Controlled Knowledge Management

Implements hybrid storage strategy:
- Operational data: workflow_states, checkpoints (temporary)
- Cognitive knowledge: validated insights, patterns (permanent)
- Quality filtering: prevents knowledge pollution
"""

import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from arango import ArangoClient


from .shared.logging_manager import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowInsight:
    """Represents a validated insight extracted from workflow execution."""

    pattern_type: str  # "optimization", "failure_prevention", "configuration", "performance"
    title: str
    description: str
    evidence: List[str]
    conditions: List[str]
    impact_metrics: Dict[str, Any]
    quality_score: float
    confidence_score: float
    knowledge_domain: str = "operational"


@dataclass
class QualityMetrics:
    """Quality assessment metrics for workflow results."""

    quality_score: float
    execution_time: float
    error_count: int
    user_satisfaction: Optional[float] = None
    objective_metrics: Dict[str, Any] = None


class CognitiveDatabase:
    """
    Enhanced database client that implements quality-controlled knowledge management
    alongside operational workflow data storage.
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
        self._connected = False

        # Quality thresholds for knowledge storage
        self.COGNITIVE_CONCEPT_THRESHOLD = 7.0  # Store as validated knowledge
        self.AGENT_MEMORY_THRESHOLD = 5.0  # Store as learning pattern
        self.MINIMUM_STORAGE_THRESHOLD = 5.0  # Below this, don't store

    async def connect(self) -> bool:
        """Connect to ArangoDB and ensure required collections exist."""
        try:
            self.client = ArangoClient(hosts=self.host)
            self.db = self.client.db(
                self.database_name, username=self.username, password=self.password
            )

            # Ensure operational collections exist (temporary storage)
            await self._ensure_operational_collections()

            # Ensure cognitive collections exist (permanent knowledge)
            await self._ensure_cognitive_collections()

            self._connected = True
            logger.info(f"Connected to cognitive database at {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to cognitive database: {e}")
            return False

    async def _ensure_operational_collections(self):
        """Ensure operational collections exist for temporary workflow data."""
        operational_collections = [
            "workflow_states",
            "workflow_checkpoints",
            "plugin_states",
            "execution_history",
        ]

        for collection_name in operational_collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                logger.info(f"Created operational collection: {collection_name}")

    async def _ensure_cognitive_collections(self):
        """Ensure cognitive collections exist for permanent knowledge storage."""
        # These are the primary collections from the cognitive database guide
        cognitive_collections = [
            "agent_memory",
            "cognitive_concepts",
            "memory_relationships",
            "semantic_relationships",
            "session_context",
            "memory_validation_rules",
            "memory_quality_metrics",
        ]

        for collection_name in cognitive_collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                logger.info(f"Created cognitive collection: {collection_name}")

        # Ensure edge collections for relationships
        edge_collections = ["memory_relationships", "semantic_relationships"]
        for edge_collection in edge_collections:
            if not self.db.has_collection(edge_collection):
                self.db.create_collection(edge_collection, edge=True)

    # ==================== OPERATIONAL DATA METHODS ====================

    async def save_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> bool:
        """Save operational workflow state for resumption/debugging."""
        if not self._connected:
            return False

        try:
            document = {
                "_key": workflow_id,
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
            }

            self.db.collection("workflow_states").insert(document, overwrite=True)
            return True

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    async def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load operational workflow state."""
        if not self._connected:
            return None

        try:
            # Use proper AQL syntax order: FOR → FILTER → SORT → LIMIT → RETURN
            cursor = self.db.aql.execute(
                """
                FOR doc IN workflow_states
                FILTER doc._key == @key
                SORT doc.timestamp DESC
                LIMIT 1
                RETURN doc
                """,
                bind_vars={"key": workflow_id},
            )

            documents = list(cursor)
            if documents:
                return documents[0]["state"]
            return None

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    async def cleanup_expired_operational_data(self) -> bool:
        """Clean up expired operational data to prevent bloat."""
        if not self._connected:
            return False

        try:
            current_time = datetime.utcnow().isoformat()

            # Clean expired workflow states
            self.db.aql.execute(
                """
                FOR doc IN workflow_states
                FILTER doc.expires_at < @current_time
                REMOVE doc IN workflow_states
                """,
                bind_vars={"current_time": current_time},
            )

            # Clean old checkpoints (keep only last 24 hours)
            cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            self.db.aql.execute(
                """
                FOR doc IN workflow_checkpoints
                FILTER doc.timestamp < @cutoff_time
                REMOVE doc IN workflow_checkpoints
                """,
                bind_vars={"cutoff_time": cutoff_time},
            )

            logger.info("Cleaned up expired operational data")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup operational data: {e}")
            return False

    # ==================== COGNITIVE KNOWLEDGE METHODS ====================

    async def store_workflow_insight(
        self, insight: WorkflowInsight, workflow_context: Dict[str, Any]
    ) -> bool:
        """Store validated workflow insight as cognitive concept."""
        if not self._connected:
            return False

        try:
            # Generate concept ID
            concept_hash = hashlib.md5(
                f"{insight.pattern_type}_{insight.title}".encode()
            ).hexdigest()[:8]
            concept_id = f"workflow_{insight.pattern_type}_{concept_hash}"

            # Create cognitive concept following the guide format
            concept = {
                "_key": concept_id,
                "concept_id": concept_id,
                "semantic_embedding": None,  # For future semantic search
                "knowledge_domain": insight.knowledge_domain,
                "concept_type": f"workflow_{insight.pattern_type}",
                "abstraction_level": "operational",
                "confidence_score": insight.confidence_score,
                "evidence_strength": self._calculate_evidence_strength(insight),
                "learning_context": {
                    "workflow_name": workflow_context.get("workflow_name"),
                    "quality_score": insight.quality_score,
                    "validation_method": "workflow_execution",
                    "sample_size": 1,  # Could be aggregated later
                },
                "knowledge_content": {
                    "title": insight.title,
                    "pattern_type": insight.pattern_type,
                    "description": insight.description,
                    "evidence": insight.evidence,
                    "conditions": insight.conditions,
                    "impact_metrics": insight.impact_metrics,
                    "original_context": workflow_context,
                },
                "created": datetime.utcnow().isoformat(),
                "last_validated": datetime.utcnow().isoformat(),
            }

            result = self.db.collection("cognitive_concepts").insert(concept)

            # Store quality metrics
            await self._store_quality_metrics(concept_id, insight)

            logger.info(f"Stored workflow insight as cognitive concept: {concept_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store workflow insight: {e}")
            return False

    async def store_learning_pattern(
        self, pattern_data: Dict[str, Any], quality_metrics: QualityMetrics
    ) -> bool:
        """Store lower-confidence patterns as agent memory for future analysis."""
        if not self._connected:
            return False

        try:
            memory = {
                "title": pattern_data.get("title", "Workflow Learning Pattern"),
                "content": pattern_data.get("description", ""),
                "tags": pattern_data.get("tags", ["workflow", "learning_pattern"]),
                "tier": "foundational",
                "foundational": False,  # Not yet validated as foundational
                "memory_type": "operational",
                "validation_status": "pending",
                "quality_score": quality_metrics.quality_score,
                "execution_context": pattern_data.get("context", {}),
                "created": datetime.utcnow().isoformat(),
            }

            result = self.db.collection("agent_memory").insert(memory)
            logger.info(f"Stored learning pattern as agent memory: {result['_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to store learning pattern: {e}")
            return False

    async def _store_quality_metrics(
        self, concept_id: str, insight: WorkflowInsight
    ) -> bool:
        """Store quality metrics for tracking and validation."""
        try:
            metrics = {
                "concept_id": concept_id,
                "quality_score": insight.quality_score,
                "confidence_score": insight.confidence_score,
                "evidence_count": len(insight.evidence),
                "condition_count": len(insight.conditions),
                "impact_metrics": insight.impact_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.db.collection("memory_quality_metrics").insert(metrics)
            return True

        except Exception as e:
            logger.error(f"Failed to store quality metrics: {e}")
            return False

    def _calculate_evidence_strength(self, insight: WorkflowInsight) -> str:
        """Calculate evidence strength based on insight characteristics."""
        evidence_count = len(insight.evidence)
        condition_count = len(insight.conditions)

        if insight.quality_score >= 8.0 and evidence_count >= 3:
            return "high"
        elif insight.quality_score >= 7.0 and evidence_count >= 2:
            return "medium"
        else:
            return "low"

    # ==================== KNOWLEDGE RETRIEVAL METHODS ====================

    async def find_related_patterns(
        self, pattern_type: str, knowledge_domain: str = "operational"
    ) -> List[Dict[str, Any]]:
        """Find related workflow patterns using graph traversal."""
        if not self._connected:
            return []

        try:
            # Use proper AQL syntax with graph traversal
            cursor = self.db.aql.execute(
                """
                FOR concept IN cognitive_concepts
                FILTER concept.concept_type LIKE @pattern_type
                AND concept.knowledge_domain == @domain
                AND concept.confidence_score > 0.7
                FOR related IN 1..2 OUTBOUND concept semantic_relationships
                FILTER related.confidence_score > 0.6
                SORT concept.confidence_score DESC, related.confidence_score DESC
                LIMIT 10
                RETURN {
                    concept: concept,
                    related: related,
                    relationship_strength: related.confidence_score
                }
                """,
                bind_vars={
                    "pattern_type": f"%{pattern_type}%",
                    "domain": knowledge_domain,
                },
            )

            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to find related patterns: {e}")
            return []

    async def get_workflow_insights(
        self, workflow_name: str, min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get validated insights for a specific workflow type."""
        if not self._connected:
            return []

        try:
            cursor = self.db.aql.execute(
                """
                FOR concept IN cognitive_concepts
                FILTER concept.learning_context.workflow_name == @workflow_name
                AND concept.confidence_score >= @min_confidence
                SORT concept.confidence_score DESC, concept.created DESC
                LIMIT 20
                RETURN concept
                """,
                bind_vars={
                    "workflow_name": workflow_name,
                    "min_confidence": min_confidence,
                },
            )

            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to get workflow insights: {e}")
            return []

    # ==================== QUALITY ASSESSMENT METHODS ====================

    async def assess_workflow_quality(
        self, workflow_result: Dict[str, Any]
    ) -> QualityMetrics:
        """Assess workflow quality using multiple metrics."""
        quality_score = workflow_result.get("quality_score", 0.0)
        execution_time = workflow_result.get("execution_time", 0.0)
        error_count = len(workflow_result.get("errors", []))

        # Additional quality indicators
        success = workflow_result.get("success", False)
        if not success:
            quality_score = min(quality_score, 4.0)  # Cap failed workflows

        # Adjust for execution efficiency
        if execution_time > 120:  # > 2 minutes
            quality_score *= 0.9  # Slight penalty for slow execution

        return QualityMetrics(
            quality_score=quality_score,
            execution_time=execution_time,
            error_count=error_count,
            objective_metrics=workflow_result.get("metrics", {}),
        )

    async def should_store_as_knowledge(
        self, quality_metrics: QualityMetrics
    ) -> tuple[bool, str]:
        """Determine if workflow result should be stored as knowledge."""
        if quality_metrics.quality_score >= self.COGNITIVE_CONCEPT_THRESHOLD:
            return True, "cognitive_concept"
        elif quality_metrics.quality_score >= self.AGENT_MEMORY_THRESHOLD:
            return True, "agent_memory"
        else:
            return False, "no_storage"

    # ==================== INSIGHT EXTRACTION METHODS ====================

    def extract_workflow_insights(
        self, workflow_result: Dict[str, Any], quality_metrics: QualityMetrics
    ) -> List[WorkflowInsight]:
        """Extract actionable insights from successful workflow execution."""
        insights = []

        # Performance optimization insights
        if quality_metrics.execution_time < 30 and quality_metrics.quality_score >= 8:
            insights.append(
                WorkflowInsight(
                    pattern_type="performance",
                    title=f"Fast {workflow_result.get('workflow_name', 'workflow')} execution",
                    description=f"Achieved {quality_metrics.quality_score}/10 quality in {quality_metrics.execution_time}s",
                    evidence=[
                        f"Quality score: {quality_metrics.quality_score}",
                        f"Execution time: {quality_metrics.execution_time}s",
                        f"Error count: {quality_metrics.error_count}",
                    ],
                    conditions=[
                        f"Workflow: {workflow_result.get('workflow_name')}",
                        f"Input size: {workflow_result.get('input_size', 'unknown')}",
                    ],
                    impact_metrics={
                        "time_saved": 60 - quality_metrics.execution_time,
                        "quality_maintained": quality_metrics.quality_score >= 8,
                    },
                    quality_score=quality_metrics.quality_score,
                    confidence_score=0.8,
                )
            )

        # Configuration optimization insights
        if workflow_result.get("model_usage"):
            model_performance = workflow_result["model_usage"]
            for model, metrics in model_performance.items():
                if metrics.get("efficiency_score", 0) > 0.8:
                    insights.append(
                        WorkflowInsight(
                            pattern_type="configuration",
                            title=f"Effective {model} usage pattern",
                            description=f"Model {model} achieved high efficiency for this task type",
                            evidence=[
                                f"Efficiency score: {metrics.get('efficiency_score')}",
                                f"Cost per quality point: {metrics.get('cost_efficiency')}",
                            ],
                            conditions=[
                                f"Task type: {workflow_result.get('task_type')}",
                                f"Input complexity: {workflow_result.get('complexity')}",
                            ],
                            impact_metrics=metrics,
                            quality_score=quality_metrics.quality_score,
                            confidence_score=0.7,
                        )
                    )

        return insights

    async def disconnect(self):
        """Clean disconnect from database."""
        self._connected = False
        logger.info("Disconnected from cognitive database")


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
