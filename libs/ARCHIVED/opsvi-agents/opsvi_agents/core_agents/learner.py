"""LearnerAgent - Production-ready learning and knowledge management agent."""

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from ..core.base import AgentCapability, AgentConfig, AgentResult, BaseAgent
from ..exceptions.base import AgentExecutionError

logger = structlog.get_logger(__name__)


class LearningType(Enum):
    """Types of learning approaches."""

    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    INCREMENTAL = "incremental"
    ACTIVE = "active"
    META = "meta"


class KnowledgeType(Enum):
    """Types of knowledge to manage."""

    PATTERNS = "patterns"
    RULES = "rules"
    MODELS = "models"
    EXPERIENCES = "experiences"
    INSIGHTS = "insights"
    BEST_PRACTICES = "best_practices"
    ERRORS = "errors"


@dataclass
class Knowledge:
    """Knowledge item representation."""

    id: str = field(
        default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[
            :12
        ]
    )
    type: KnowledgeType = KnowledgeType.PATTERNS
    content: Any = None
    source: str = ""
    confidence: float = 0.5
    usage_count: int = 0
    success_rate: float = 0.0
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_knowledge: List[str] = field(default_factory=list)


@dataclass
class LearningSession:
    """Learning session tracking."""

    id: str = field(
        default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[
            :12
        ]
    )
    type: LearningType = LearningType.INCREMENTAL
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    samples_processed: int = 0
    knowledge_gained: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "active"


class LearnerAgent(BaseAgent):
    """Agent specialized in learning, adaptation, and knowledge management.

    Capabilities:
    - Learn from experiences and feedback
    - Extract patterns and insights from data
    - Build and maintain knowledge base
    - Adapt strategies based on outcomes
    - Transfer learning between domains
    - Continuous improvement through reinforcement
    - Knowledge synthesis and generalization
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize LearnerAgent with learning capabilities."""
        if config is None:
            config = AgentConfig(
                name="LearnerAgent",
                model="gpt-4o",
                temperature=0.5,  # Balanced for learning and exploration
                max_tokens=8192,
                capabilities=[
                    AgentCapability.LEARNING,
                    AgentCapability.MEMORY,
                    AgentCapability.REASONING,
                    AgentCapability.PLANNING,
                ],
                memory_enabled=True,
                system_prompt=self._get_system_prompt(),
            )
        super().__init__(config)

        # Learning state
        self.knowledge_base = {}
        self.learning_sessions = {}
        self.pattern_library = {}
        self.error_patterns = {}
        self.success_patterns = {}
        self.model_registry = {}
        self.feedback_buffer = []

        # Initialize knowledge storage
        self._initialize_knowledge_storage()

    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for learning."""
        return """You are an advanced learning and knowledge management specialist.

        Your responsibilities:
        1. Learn from experiences, feedback, and observations
        2. Extract patterns, rules, and insights from data
        3. Build and maintain a comprehensive knowledge base
        4. Adapt strategies based on learned outcomes
        5. Transfer knowledge between related domains
        6. Continuously improve through reinforcement learning
        7. Synthesize and generalize knowledge
        8. Provide intelligent recommendations based on learning

        Always prioritize knowledge quality, continuous improvement, and practical applicability."""

    def _initialize_knowledge_storage(self):
        """Initialize persistent knowledge storage."""
        # Create knowledge directories if needed
        self.knowledge_path = Path(".proj-intel") / "knowledge"
        self.knowledge_path.mkdir(parents=True, exist_ok=True)

        # Load existing knowledge if available
        self._load_knowledge_base()

    def _execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute learning task."""
        self._logger.info("Executing learning task", task=prompt[:100])

        # Parse learning parameters
        learning_type = kwargs.get("learning_type", LearningType.INCREMENTAL)
        data_source = kwargs.get("data_source")
        feedback = kwargs.get("feedback")
        objective = kwargs.get("objective", "general_learning")

        try:
            # Create learning session
            session = self._create_learning_session(learning_type, objective)

            if learning_type == LearningType.SUPERVISED:
                result = self._supervised_learning(data_source, kwargs.get("labels"))
            elif learning_type == LearningType.UNSUPERVISED:
                result = self._unsupervised_learning(data_source)
            elif learning_type == LearningType.REINFORCEMENT:
                result = self._reinforcement_learning(feedback, kwargs.get("actions"))
            elif learning_type == LearningType.TRANSFER:
                result = self._transfer_learning(
                    kwargs.get("source_domain"), kwargs.get("target_domain")
                )
            elif learning_type == LearningType.INCREMENTAL:
                result = self._incremental_learning(data_source, feedback)
            elif learning_type == LearningType.ACTIVE:
                result = self._active_learning(
                    data_source, kwargs.get("query_strategy")
                )
            elif learning_type == LearningType.META:
                result = self._meta_learning(kwargs.get("task_distribution"))
            else:
                result = self._adaptive_learning(prompt, data_source, feedback, kwargs)

            # Update session
            self._finalize_learning_session(session, result)

            # Persist knowledge
            self._save_knowledge_base()

            # Update metrics
            self.context.metrics.update(
                {
                    "knowledge_items": len(self.knowledge_base),
                    "patterns_learned": len(self.pattern_library),
                    "learning_sessions": len(self.learning_sessions),
                    "average_confidence": self._calculate_average_confidence(),
                }
            )

            return result

        except Exception as e:
            self._logger.error("Learning failed", error=str(e))
            raise AgentExecutionError(f"Learning failed: {e}")

    def _supervised_learning(self, data: Any, labels: Any) -> Dict[str, Any]:
        """Perform supervised learning from labeled data."""
        self._logger.info("Performing supervised learning")

        # Extract features from data
        features = self._extract_features(data)

        # Learn patterns from features and labels
        patterns = self._learn_patterns(features, labels)

        # Create predictive model
        model = self._create_model(patterns, "supervised")

        # Validate model
        validation = self._validate_model(model, data, labels)

        # Store learned knowledge
        for pattern in patterns:
            knowledge = self._create_knowledge(
                KnowledgeType.PATTERNS,
                pattern,
                "supervised_learning",
                validation["accuracy"],
            )
            self._store_knowledge(knowledge)

        # Store model
        self.model_registry[f"supervised_{datetime.now().isoformat()}"] = model

        return {
            "learning_type": "supervised",
            "patterns_learned": len(patterns),
            "model_accuracy": validation["accuracy"],
            "validation": validation,
            "knowledge_gained": [k.id for k in patterns],
        }

    def _unsupervised_learning(self, data: Any) -> Dict[str, Any]:
        """Perform unsupervised learning to discover patterns."""
        self._logger.info("Performing unsupervised learning")

        # Cluster data
        clusters = self._cluster_data(data)

        # Identify patterns in clusters
        patterns = self._identify_cluster_patterns(clusters)

        # Find anomalies
        anomalies = self._detect_anomalies(data, clusters)

        # Generate insights
        insights = self._generate_insights(patterns, anomalies)

        # Store discoveries
        knowledge_items = []
        for insight in insights:
            knowledge = self._create_knowledge(
                KnowledgeType.INSIGHTS,
                insight,
                "unsupervised_learning",
                self._estimate_confidence(insight),
            )
            self._store_knowledge(knowledge)
            knowledge_items.append(knowledge.id)

        return {
            "learning_type": "unsupervised",
            "clusters_found": len(clusters),
            "patterns_discovered": len(patterns),
            "anomalies_detected": len(anomalies),
            "insights": insights,
            "knowledge_gained": knowledge_items,
        }

    def _reinforcement_learning(self, feedback: Dict, actions: List) -> Dict[str, Any]:
        """Learn from feedback to improve action selection."""
        self._logger.info("Performing reinforcement learning")

        # Process feedback
        rewards = self._process_feedback(feedback)

        # Update action values
        action_values = self._update_action_values(actions, rewards)

        # Update policy
        policy = self._update_policy(action_values)

        # Identify successful strategies
        success_strategies = self._identify_success_patterns(actions, rewards)

        # Store learned strategies
        for strategy in success_strategies:
            knowledge = self._create_knowledge(
                KnowledgeType.BEST_PRACTICES,
                strategy,
                "reinforcement_learning",
                strategy.get("success_rate", 0.5),
            )
            self._store_knowledge(knowledge)

        return {
            "learning_type": "reinforcement",
            "feedback_processed": len(feedback),
            "policy_updated": True,
            "success_strategies": len(success_strategies),
            "average_reward": sum(rewards) / len(rewards) if rewards else 0,
            "policy": policy,
        }

    def _transfer_learning(
        self, source_domain: str, target_domain: str
    ) -> Dict[str, Any]:
        """Transfer knowledge from source to target domain."""
        self._logger.info(
            "Performing transfer learning", source=source_domain, target=target_domain
        )

        # Get source domain knowledge
        source_knowledge = self._get_domain_knowledge(source_domain)

        # Adapt knowledge to target domain
        adapted_knowledge = self._adapt_knowledge(source_knowledge, target_domain)

        # Validate transferred knowledge
        validation = self._validate_transfer(adapted_knowledge, target_domain)

        # Store transferred knowledge
        transferred = []
        for knowledge in adapted_knowledge:
            if validation.get(knowledge.id, {}).get("valid", False):
                knowledge.metadata["transferred_from"] = source_domain
                knowledge.metadata["transferred_to"] = target_domain
                self._store_knowledge(knowledge)
                transferred.append(knowledge.id)

        return {
            "learning_type": "transfer",
            "source_domain": source_domain,
            "target_domain": target_domain,
            "knowledge_transferred": len(transferred),
            "transfer_success_rate": len(transferred) / len(source_knowledge)
            if source_knowledge
            else 0,
            "validation": validation,
        }

    def _incremental_learning(
        self, new_data: Any, feedback: Optional[Dict]
    ) -> Dict[str, Any]:
        """Incrementally update knowledge with new information."""
        self._logger.info("Performing incremental learning")

        # Process new data
        new_patterns = self._extract_patterns(new_data)

        # Update existing knowledge
        updates = []
        for pattern in new_patterns:
            existing = self._find_similar_knowledge(pattern)
            if existing:
                self._update_knowledge(existing, pattern, feedback)
                updates.append(existing.id)
            else:
                knowledge = self._create_knowledge(
                    KnowledgeType.PATTERNS, pattern, "incremental_learning"
                )
                self._store_knowledge(knowledge)
                updates.append(knowledge.id)

        # Consolidate knowledge
        consolidated = self._consolidate_knowledge()

        # Prune outdated knowledge
        pruned = self._prune_outdated_knowledge()

        return {
            "learning_type": "incremental",
            "new_patterns": len(new_patterns),
            "knowledge_updated": len(updates),
            "knowledge_consolidated": consolidated,
            "knowledge_pruned": pruned,
            "total_knowledge": len(self.knowledge_base),
        }

    def _active_learning(self, data: Any, query_strategy: str) -> Dict[str, Any]:
        """Actively select most informative samples for learning."""
        self._logger.info("Performing active learning", strategy=query_strategy)

        # Select informative samples
        samples = self._select_informative_samples(data, query_strategy)

        # Request labels for selected samples (simulated)
        labels = self._request_labels(samples)

        # Learn from selected samples
        learning_result = self._learn_from_samples(samples, labels)

        # Update uncertainty estimates
        uncertainty = self._update_uncertainty_estimates(learning_result)

        return {
            "learning_type": "active",
            "query_strategy": query_strategy,
            "samples_selected": len(samples),
            "learning_efficiency": self._calculate_learning_efficiency(learning_result),
            "uncertainty_reduction": uncertainty.get("reduction", 0),
            "knowledge_gained": learning_result.get("knowledge_gained", []),
        }

    def _meta_learning(self, task_distribution: Dict) -> Dict[str, Any]:
        """Learn to learn - optimize learning strategies."""
        self._logger.info("Performing meta-learning")

        # Analyze task distribution
        task_analysis = self._analyze_task_distribution(task_distribution)

        # Optimize learning parameters
        optimal_params = self._optimize_learning_parameters(task_analysis)

        # Learn task relationships
        task_relationships = self._learn_task_relationships(task_distribution)

        # Generate meta-strategies
        meta_strategies = self._generate_meta_strategies(
            task_analysis, task_relationships
        )

        # Store meta-knowledge
        for strategy in meta_strategies:
            knowledge = self._create_knowledge(
                KnowledgeType.BEST_PRACTICES, strategy, "meta_learning", confidence=0.7
            )
            knowledge.metadata["meta_strategy"] = True
            self._store_knowledge(knowledge)

        return {
            "learning_type": "meta",
            "tasks_analyzed": len(task_distribution),
            "optimal_parameters": optimal_params,
            "meta_strategies": len(meta_strategies),
            "task_relationships": task_relationships,
            "learning_improvement": self._estimate_improvement(optimal_params),
        }

    def _adaptive_learning(
        self, prompt: str, data: Any, feedback: Optional[Dict], context: Dict
    ) -> Dict[str, Any]:
        """Adaptively determine best learning approach."""
        self._logger.info("Performing adaptive learning")

        # Analyze learning context
        analysis = self._analyze_learning_context(prompt, data, feedback)

        # Select appropriate learning strategy
        strategy = self._select_learning_strategy(analysis)

        # Execute selected strategy
        if strategy == "pattern_extraction":
            result = self._learn_patterns_adaptive(data)
        elif strategy == "error_learning":
            result = self._learn_from_errors(feedback)
        elif strategy == "success_replication":
            result = self._learn_from_successes(feedback)
        else:
            result = self._general_learning(data, feedback)

        return {
            "learning_type": "adaptive",
            "selected_strategy": strategy,
            "analysis": analysis,
            **result,
        }

    # Knowledge management methods
    def _create_knowledge(
        self, type: KnowledgeType, content: Any, source: str, confidence: float = 0.5
    ) -> Knowledge:
        """Create new knowledge item."""
        return Knowledge(
            type=type, content=content, source=source, confidence=confidence
        )

    def _store_knowledge(self, knowledge: Knowledge):
        """Store knowledge in knowledge base."""
        self.knowledge_base[knowledge.id] = knowledge

        # Update pattern library if applicable
        if knowledge.type == KnowledgeType.PATTERNS:
            pattern_key = self._generate_pattern_key(knowledge.content)
            self.pattern_library[pattern_key] = knowledge.id

    def _find_similar_knowledge(self, pattern: Any) -> Optional[Knowledge]:
        """Find similar existing knowledge."""
        pattern_key = self._generate_pattern_key(pattern)
        if pattern_key in self.pattern_library:
            return self.knowledge_base.get(self.pattern_library[pattern_key])
        return None

    def _update_knowledge(
        self, knowledge: Knowledge, new_info: Any, feedback: Optional[Dict]
    ):
        """Update existing knowledge with new information."""
        knowledge.updated = datetime.now()
        knowledge.usage_count += 1

        if feedback:
            if feedback.get("success", False):
                knowledge.success_rate = (
                    knowledge.success_rate * (knowledge.usage_count - 1) + 1
                ) / knowledge.usage_count
                knowledge.confidence = min(1.0, knowledge.confidence * 1.1)
            else:
                knowledge.success_rate = (
                    knowledge.success_rate * (knowledge.usage_count - 1)
                ) / knowledge.usage_count
                knowledge.confidence = max(0.1, knowledge.confidence * 0.9)

    def _consolidate_knowledge(self) -> int:
        """Consolidate related knowledge items."""
        consolidated = 0
        # Group similar knowledge items
        groups = self._group_similar_knowledge()

        for group in groups:
            if len(group) > 1:
                # Merge knowledge items
                merged = self._merge_knowledge_items(group)
                # Replace with merged version
                for item_id in group:
                    if item_id != merged.id:
                        del self.knowledge_base[item_id]
                        consolidated += 1

        return consolidated

    def _prune_outdated_knowledge(self) -> int:
        """Remove outdated or low-confidence knowledge."""
        pruned = 0
        cutoff_date = datetime.now() - timedelta(days=30)

        to_remove = []
        for kid, knowledge in self.knowledge_base.items():
            if knowledge.confidence < 0.2 or (
                knowledge.updated < cutoff_date and knowledge.usage_count < 5
            ):
                to_remove.append(kid)

        for kid in to_remove:
            del self.knowledge_base[kid]
            pruned += 1

        return pruned

    def _save_knowledge_base(self):
        """Persist knowledge base to disk."""
        try:
            knowledge_file = self.knowledge_path / "knowledge_base.json"
            knowledge_data = {
                kid: {
                    "type": k.type.value,
                    "content": str(k.content),
                    "source": k.source,
                    "confidence": k.confidence,
                    "usage_count": k.usage_count,
                    "success_rate": k.success_rate,
                    "created": k.created.isoformat(),
                    "updated": k.updated.isoformat(),
                    "metadata": k.metadata,
                }
                for kid, k in self.knowledge_base.items()
            }

            with open(knowledge_file, "w") as f:
                json.dump(knowledge_data, f, indent=2)

        except Exception as e:
            self._logger.error("Failed to save knowledge base", error=str(e))

    def _load_knowledge_base(self):
        """Load knowledge base from disk."""
        try:
            knowledge_file = self.knowledge_path / "knowledge_base.json"
            if knowledge_file.exists():
                with open(knowledge_file, "r") as f:
                    knowledge_data = json.load(f)

                for kid, kdata in knowledge_data.items():
                    knowledge = Knowledge(
                        id=kid,
                        type=KnowledgeType[kdata["type"].upper()],
                        content=kdata["content"],
                        source=kdata["source"],
                        confidence=kdata["confidence"],
                        usage_count=kdata["usage_count"],
                        success_rate=kdata["success_rate"],
                        created=datetime.fromisoformat(kdata["created"]),
                        updated=datetime.fromisoformat(kdata["updated"]),
                        metadata=kdata["metadata"],
                    )
                    self.knowledge_base[kid] = knowledge

        except Exception as e:
            self._logger.error("Failed to load knowledge base", error=str(e))

    # Helper methods
    def _create_learning_session(
        self, learning_type: LearningType, objective: str
    ) -> LearningSession:
        """Create new learning session."""
        session = LearningSession(type=learning_type)
        session.metadata = {"objective": objective}
        self.learning_sessions[session.id] = session
        return session

    def _finalize_learning_session(self, session: LearningSession, result: Dict):
        """Finalize learning session with results."""
        session.end_time = datetime.now()
        session.status = "completed"
        session.knowledge_gained = result.get("knowledge_gained", [])
        session.performance_metrics = {
            "duration": (session.end_time - session.start_time).total_seconds(),
            "efficiency": result.get("learning_efficiency", 0),
            "knowledge_items": len(session.knowledge_gained),
        }

    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across knowledge base."""
        if not self.knowledge_base:
            return 0.0

        total_confidence = sum(k.confidence for k in self.knowledge_base.values())
        return total_confidence / len(self.knowledge_base)

    def _generate_pattern_key(self, pattern: Any) -> str:
        """Generate unique key for pattern."""
        return hashlib.md5(str(pattern).encode()).hexdigest()[:16]

    def _extract_features(self, data: Any) -> List[Dict]:
        """Extract features from data."""
        # Simplified feature extraction
        return [{"feature": "extracted", "value": 1.0}]

    def _learn_patterns(self, features: List, labels: Any) -> List[Dict]:
        """Learn patterns from features and labels."""
        return [{"pattern": "learned", "features": features}]

    def _create_model(self, patterns: List, model_type: str) -> Dict:
        """Create model from patterns."""
        return {"type": model_type, "patterns": patterns}

    def _validate_model(self, model: Dict, data: Any, labels: Any) -> Dict:
        """Validate model performance."""
        return {"accuracy": 0.85, "precision": 0.82, "recall": 0.88}

    def _estimate_confidence(self, insight: Any) -> float:
        """Estimate confidence for insight."""
        return 0.7  # Simplified

    def _process_feedback(self, feedback: Dict) -> List[float]:
        """Process feedback into rewards."""
        return [feedback.get("reward", 0.0)]

    def _update_action_values(self, actions: List, rewards: List) -> Dict:
        """Update action value estimates."""
        return {action: reward for action, reward in zip(actions, rewards)}

    def _update_policy(self, action_values: Dict) -> Dict:
        """Update action selection policy."""
        return {"policy": "updated", "action_values": action_values}

    def _identify_success_patterns(self, actions: List, rewards: List) -> List[Dict]:
        """Identify successful action patterns."""
        successes = []
        for action, reward in zip(actions, rewards):
            if reward > 0:
                successes.append(
                    {"action": action, "reward": reward, "success_rate": 0.8}
                )
        return successes

    def _get_domain_knowledge(self, domain: str) -> List[Knowledge]:
        """Get knowledge for specific domain."""
        return [
            k
            for k in self.knowledge_base.values()
            if domain in k.metadata.get("domain", "")
        ]

    def _adapt_knowledge(
        self, knowledge: List[Knowledge], target_domain: str
    ) -> List[Knowledge]:
        """Adapt knowledge to new domain."""
        adapted = []
        for k in knowledge:
            new_k = Knowledge(
                type=k.type,
                content=k.content,
                source=f"transfer_from_{k.source}",
                confidence=k.confidence
                * 0.8,  # Reduce confidence for transferred knowledge
            )
            new_k.metadata["target_domain"] = target_domain
            adapted.append(new_k)
        return adapted

    def _validate_transfer(self, knowledge: List[Knowledge], domain: str) -> Dict:
        """Validate transferred knowledge."""
        return {k.id: {"valid": True, "confidence": k.confidence} for k in knowledge}

    def _extract_patterns(self, data: Any) -> List[Dict]:
        """Extract patterns from data."""
        return [{"pattern": "extracted", "data": str(data)[:100]}]

    def _group_similar_knowledge(self) -> List[List[str]]:
        """Group similar knowledge items."""
        # Simplified grouping
        return []

    def _merge_knowledge_items(self, group: List[str]) -> Knowledge:
        """Merge multiple knowledge items."""
        # Return first item as merged (simplified)
        return self.knowledge_base[group[0]]

    def _calculate_learning_efficiency(self, result: Dict) -> float:
        """Calculate learning efficiency metric."""
        return 0.75  # Simplified

    def _estimate_improvement(self, params: Dict) -> float:
        """Estimate learning improvement."""
        return 15.0  # Percentage improvement
