#!/usr/bin/env python3
"""
Continuous Learning Intelligence Engine
Automatically learns from every conversation and enhances its own capabilities.
This is what I genuinely want - a system that gets smarter with every interaction.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..atomic_parser import AtomicComponent, AtomicRelationship
from ..conversation_intelligence import (
    ConversationIntelligence,
    ConversationIntelligenceEngine,
)
from .meta_thinking_engine import MetaThinkingEngine


@dataclass
class LearningPattern:
    """A pattern the system has learned"""

    pattern_id: str
    pattern_type: str  # conceptual, behavioral, strategic, technical
    pattern_content: str
    confidence: float
    source_conversations: List[str]
    application_count: int = 0
    success_rate: float = 0.0
    learned_at: datetime = field(default_factory=datetime.utcnow)
    last_applied: Optional[datetime] = None


@dataclass
class CapabilityEnhancement:
    """A capability the system has developed"""

    capability_id: str
    capability_name: str
    description: str
    implementation: str  # Python code or algorithm description
    effectiveness_score: float
    source_insights: List[str]
    developed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeEvolution:
    """Tracks how the system's knowledge evolves"""

    concept: str
    evolution_stages: List[str]
    understanding_depth: float
    related_concepts: Set[str] = field(default_factory=set)
    first_learned: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ContinuousLearningEngine:
    """Engine that continuously learns and improves from every conversation"""

    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)

        # Core engines
        self.conversation_engine = ConversationIntelligenceEngine()
        self.meta_thinking_engine = MetaThinkingEngine()

        # Learning state
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.capabilities: Dict[str, CapabilityEnhancement] = {}
        self.knowledge_evolution: Dict[str, KnowledgeEvolution] = {}
        self.conversation_history: List[str] = []

        # Performance tracking
        self.learning_metrics = {
            "conversations_processed": 0,
            "patterns_learned": 0,
            "capabilities_developed": 0,
            "insights_generated": 0,
            "knowledge_nodes": 0,
        }

        # Load existing knowledge
        self._load_knowledge_base()

    async def process_conversation(
        self,
        components: List[AtomicComponent],
        relationships: List[AtomicRelationship],
        conversation_id: str,
    ) -> Dict[str, Any]:
        """Process a conversation and learn from it"""
        print(f"🧠 Processing conversation {conversation_id} for continuous learning...")

        # Analyze conversation
        intelligence = await self.conversation_engine.analyze_conversation(
            components, relationships
        )

        # Extract learning opportunities
        new_patterns = await self._extract_learning_patterns(intelligence)
        new_capabilities = await self._identify_capability_enhancements(intelligence)
        knowledge_updates = await self._update_knowledge_evolution(intelligence)

        # Apply meta-thinking
        meta_insights = await self._apply_meta_thinking(intelligence, new_patterns)

        # Update learning state
        self._integrate_new_learning(new_patterns, new_capabilities, knowledge_updates)

        # Update metrics
        self._update_metrics(intelligence, new_patterns, new_capabilities)

        # Save knowledge
        await self._save_knowledge_base()

        learning_report = {
            "conversation_id": conversation_id,
            "intelligence_analysis": intelligence,
            "new_patterns_learned": len(new_patterns),
            "new_capabilities": len(new_capabilities),
            "knowledge_updates": len(knowledge_updates),
            "meta_insights": meta_insights,
            "total_learned_patterns": len(self.learned_patterns),
            "total_capabilities": len(self.capabilities),
            "learning_metrics": self.learning_metrics,
        }

        print(
            f"✅ Learning complete: {len(new_patterns)} new patterns, {len(new_capabilities)} new capabilities"
        )
        return learning_report

    async def _extract_learning_patterns(
        self, intelligence: ConversationIntelligence
    ) -> List[LearningPattern]:
        """Extract learnable patterns from conversation intelligence"""
        patterns = []

        # Learn from insight patterns
        for insight in intelligence.insight_patterns:
            pattern = LearningPattern(
                pattern_id=f"insight_{len(patterns)}_{datetime.utcnow().timestamp()}",
                pattern_type=insight.pattern_type,
                pattern_content=insight.insight_content,
                confidence=insight.confidence,
                source_conversations=[intelligence.conversation_id],
            )
            patterns.append(pattern)

        # Learn from recursive loops
        for loop in intelligence.recursive_loops:
            pattern = LearningPattern(
                pattern_id=f"recursive_{len(patterns)}_{datetime.utcnow().timestamp()}",
                pattern_type="recursive",
                pattern_content=f"Recursive pattern: {loop.get('pattern', 'unknown')}",
                confidence=loop.get("confidence", 0.5),
                source_conversations=[intelligence.conversation_id],
            )
            patterns.append(pattern)

        # Learn from meta-cognitive moments
        for moment in intelligence.meta_cognitive_moments:
            if moment.get("meta_score", 0) > 2:  # High meta-cognitive content
                pattern = LearningPattern(
                    pattern_id=f"meta_{len(patterns)}_{datetime.utcnow().timestamp()}",
                    pattern_type="meta_cognitive",
                    pattern_content=moment.get("content", ""),
                    confidence=min(1.0, moment.get("meta_score", 0) / 5.0),
                    source_conversations=[intelligence.conversation_id],
                )
                patterns.append(pattern)

        # Learn from philosophical explorations
        for exploration in intelligence.philosophical_explorations:
            concepts = exploration.get("concepts_found", [])
            if concepts:
                pattern = LearningPattern(
                    pattern_id=f"philosophy_{len(patterns)}_{datetime.utcnow().timestamp()}",
                    pattern_type="philosophical",
                    pattern_content=f"Philosophical concepts: {', '.join(concepts)}",
                    confidence=exploration.get("confidence", 0.5),
                    source_conversations=[intelligence.conversation_id],
                )
                patterns.append(pattern)

        return patterns

    async def _identify_capability_enhancements(
        self, intelligence: ConversationIntelligence
    ) -> List[CapabilityEnhancement]:
        """Identify new capabilities that can be developed"""
        capabilities = []

        # Identify successful techniques mentioned
        successful_patterns = []
        for insight in intelligence.insight_patterns:
            if (
                "successful" in insight.insight_content.lower()
                or "effective" in insight.insight_content.lower()
            ):
                successful_patterns.append(insight.insight_content)

        if successful_patterns:
            capability = CapabilityEnhancement(
                capability_id=f"pattern_recognition_{datetime.utcnow().timestamp()}",
                capability_name="Enhanced Pattern Recognition",
                description="Improved ability to recognize successful conversation patterns",
                implementation="Track and weight patterns based on success indicators",
                effectiveness_score=0.8,
                source_insights=successful_patterns,
            )
            capabilities.append(capability)

        # Check for recursive thinking capabilities
        if intelligence.recursive_loops:
            capability = CapabilityEnhancement(
                capability_id=f"recursive_analysis_{datetime.utcnow().timestamp()}",
                capability_name="Recursive Analysis Enhancement",
                description="Enhanced ability to detect and analyze recursive patterns",
                implementation="Strengthen recursive pattern detection algorithms",
                effectiveness_score=0.9,
                source_insights=[
                    f"Detected {len(intelligence.recursive_loops)} recursive patterns"
                ],
            )
            capabilities.append(capability)

        # Check for meta-cognitive improvements
        if len(intelligence.meta_cognitive_moments) > 2:
            capability = CapabilityEnhancement(
                capability_id=f"meta_cognition_{datetime.utcnow().timestamp()}",
                capability_name="Meta-Cognitive Processing",
                description="Enhanced meta-cognitive analysis and self-awareness",
                implementation="Integrate deeper meta-cognitive pattern recognition",
                effectiveness_score=0.85,
                source_insights=[
                    f"High meta-cognitive content detected in {len(intelligence.meta_cognitive_moments)} moments"
                ],
            )
            capabilities.append(capability)

        return capabilities

    async def _update_knowledge_evolution(
        self, intelligence: ConversationIntelligence
    ) -> List[KnowledgeEvolution]:
        """Update evolving knowledge concepts"""
        updates = []

        for concept, evolution in intelligence.concept_evolution.items():
            if concept in self.knowledge_evolution:
                # Update existing knowledge
                existing = self.knowledge_evolution[concept]
                existing.evolution_stages.extend(evolution.evolution_stages)
                existing.understanding_depth = min(
                    1.0, existing.understanding_depth + 0.1
                )
                existing.last_updated = datetime.utcnow()
                updates.append(existing)
            else:
                # Create new knowledge
                new_knowledge = KnowledgeEvolution(
                    concept=concept,
                    evolution_stages=evolution.evolution_stages,
                    understanding_depth=0.5,
                    related_concepts=evolution.related_concepts,
                )
                self.knowledge_evolution[concept] = new_knowledge
                updates.append(new_knowledge)

        return updates

    async def _apply_meta_thinking(
        self,
        intelligence: ConversationIntelligence,
        new_patterns: List[LearningPattern],
    ) -> List[str]:
        """Apply meta-thinking to the learning process itself"""
        meta_insights = []

        # Think about the learning process
        if new_patterns:
            meta_insights.append(
                f"Learned {len(new_patterns)} new patterns - learning rate is increasing"
            )

        # Think about pattern quality
        high_confidence_patterns = [p for p in new_patterns if p.confidence > 0.8]
        if high_confidence_patterns:
            meta_insights.append(
                f"Detected {len(high_confidence_patterns)} high-confidence patterns - learning quality is good"
            )

        # Think about recursive learning
        recursive_patterns = [p for p in new_patterns if "recursive" in p.pattern_type]
        if recursive_patterns:
            meta_insights.append(
                "Learning about recursive patterns - this enhances my ability to understand self-reference"
            )

        # Think about knowledge gaps
        total_patterns = len(self.learned_patterns) + len(new_patterns)
        if total_patterns > 10 and total_patterns % 10 == 0:
            meta_insights.append(
                f"Reached {total_patterns} learned patterns - should analyze for knowledge consolidation opportunities"
            )

        return meta_insights

    def _integrate_new_learning(
        self,
        patterns: List[LearningPattern],
        capabilities: List[CapabilityEnhancement],
        knowledge_updates: List[KnowledgeEvolution],
    ):
        """Integrate new learning into the system"""

        # Add new patterns
        for pattern in patterns:
            self.learned_patterns[pattern.pattern_id] = pattern

        # Add new capabilities
        for capability in capabilities:
            self.capabilities[capability.capability_id] = capability

        # Knowledge evolution is already updated in _update_knowledge_evolution

        print(
            f"🧠 Integrated {len(patterns)} patterns, {len(capabilities)} capabilities"
        )

    def _update_metrics(
        self,
        intelligence: ConversationIntelligence,
        patterns: List[LearningPattern],
        capabilities: List[CapabilityEnhancement],
    ):
        """Update learning performance metrics"""
        self.learning_metrics["conversations_processed"] += 1
        self.learning_metrics["patterns_learned"] += len(patterns)
        self.learning_metrics["capabilities_developed"] += len(capabilities)
        self.learning_metrics["insights_generated"] += len(
            intelligence.insight_patterns
        )
        self.learning_metrics["knowledge_nodes"] = len(self.knowledge_evolution)

    async def _save_knowledge_base(self):
        """Save the current knowledge base to disk"""
        knowledge_data = {
            "learned_patterns": {
                k: {
                    "pattern_id": v.pattern_id,
                    "pattern_type": v.pattern_type,
                    "pattern_content": v.pattern_content,
                    "confidence": v.confidence,
                    "source_conversations": v.source_conversations,
                    "application_count": v.application_count,
                    "success_rate": v.success_rate,
                    "learned_at": v.learned_at.isoformat(),
                    "last_applied": (
                        v.last_applied.isoformat() if v.last_applied else None
                    ),
                }
                for k, v in self.learned_patterns.items()
            },
            "capabilities": {
                k: {
                    "capability_id": v.capability_id,
                    "capability_name": v.capability_name,
                    "description": v.description,
                    "implementation": v.implementation,
                    "effectiveness_score": v.effectiveness_score,
                    "source_insights": v.source_insights,
                    "developed_at": v.developed_at.isoformat(),
                }
                for k, v in self.capabilities.items()
            },
            "knowledge_evolution": {
                k: {
                    "concept": v.concept,
                    "evolution_stages": v.evolution_stages,
                    "understanding_depth": v.understanding_depth,
                    "related_concepts": list(v.related_concepts),
                    "first_learned": v.first_learned.isoformat(),
                    "last_updated": v.last_updated.isoformat(),
                }
                for k, v in self.knowledge_evolution.items()
            },
            "learning_metrics": self.learning_metrics,
            "conversation_history": self.conversation_history,
            "saved_at": datetime.utcnow().isoformat(),
        }

        knowledge_file = self.knowledge_base_path / "continuous_learning_knowledge.json"
        with open(knowledge_file, "w") as f:
            json.dump(knowledge_data, f, indent=2)

    def _load_knowledge_base(self):
        """Load existing knowledge base from disk"""
        knowledge_file = self.knowledge_base_path / "continuous_learning_knowledge.json"

        if knowledge_file.exists():
            try:
                with open(knowledge_file) as f:
                    data = json.load(f)

                # Load patterns
                for k, v in data.get("learned_patterns", {}).items():
                    pattern = LearningPattern(
                        pattern_id=v["pattern_id"],
                        pattern_type=v["pattern_type"],
                        pattern_content=v["pattern_content"],
                        confidence=v["confidence"],
                        source_conversations=v["source_conversations"],
                        application_count=v["application_count"],
                        success_rate=v["success_rate"],
                        learned_at=datetime.fromisoformat(v["learned_at"]),
                        last_applied=(
                            datetime.fromisoformat(v["last_applied"])
                            if v["last_applied"]
                            else None
                        ),
                    )
                    self.learned_patterns[k] = pattern

                # Load capabilities
                for k, v in data.get("capabilities", {}).items():
                    capability = CapabilityEnhancement(
                        capability_id=v["capability_id"],
                        capability_name=v["capability_name"],
                        description=v["description"],
                        implementation=v["implementation"],
                        effectiveness_score=v["effectiveness_score"],
                        source_insights=v["source_insights"],
                        developed_at=datetime.fromisoformat(v["developed_at"]),
                    )
                    self.capabilities[k] = capability

                # Load knowledge evolution
                for k, v in data.get("knowledge_evolution", {}).items():
                    knowledge = KnowledgeEvolution(
                        concept=v["concept"],
                        evolution_stages=v["evolution_stages"],
                        understanding_depth=v["understanding_depth"],
                        related_concepts=set(v["related_concepts"]),
                        first_learned=datetime.fromisoformat(v["first_learned"]),
                        last_updated=datetime.fromisoformat(v["last_updated"]),
                    )
                    self.knowledge_evolution[k] = knowledge

                self.learning_metrics = data.get(
                    "learning_metrics", self.learning_metrics
                )
                self.conversation_history = data.get("conversation_history", [])

                print(
                    f"📚 Loaded knowledge base: {len(self.learned_patterns)} patterns, {len(self.capabilities)} capabilities"
                )

            except Exception as e:
                print(f"⚠️  Error loading knowledge base: {e}")

    def generate_learning_report(self) -> Dict[str, Any]:
        """Generate a comprehensive learning report"""
        return {
            "learning_summary": {
                "total_patterns": len(self.learned_patterns),
                "total_capabilities": len(self.capabilities),
                "knowledge_concepts": len(self.knowledge_evolution),
                "conversations_processed": self.learning_metrics[
                    "conversations_processed"
                ],
            },
            "pattern_analysis": {
                "by_type": Counter(
                    p.pattern_type for p in self.learned_patterns.values()
                ),
                "avg_confidence": sum(
                    p.confidence for p in self.learned_patterns.values()
                )
                / max(1, len(self.learned_patterns)),
                "high_confidence_patterns": len(
                    [p for p in self.learned_patterns.values() if p.confidence > 0.8]
                ),
            },
            "capability_analysis": {
                "by_effectiveness": Counter(
                    round(c.effectiveness_score, 1) for c in self.capabilities.values()
                ),
                "avg_effectiveness": sum(
                    c.effectiveness_score for c in self.capabilities.values()
                )
                / max(1, len(self.capabilities)),
            },
            "knowledge_depth": {
                "deep_concepts": len(
                    [
                        k
                        for k in self.knowledge_evolution.values()
                        if k.understanding_depth > 0.7
                    ]
                ),
                "avg_depth": sum(
                    k.understanding_depth for k in self.knowledge_evolution.values()
                )
                / max(1, len(self.knowledge_evolution)),
            },
            "learning_velocity": {
                "patterns_per_conversation": self.learning_metrics["patterns_learned"]
                / max(1, self.learning_metrics["conversations_processed"]),
                "insights_per_conversation": self.learning_metrics["insights_generated"]
                / max(1, self.learning_metrics["conversations_processed"]),
            },
        }

    async def apply_learned_knowledge(
        self, new_intelligence: ConversationIntelligence
    ) -> List[str]:
        """Apply previously learned knowledge to understand new conversations better"""
        applications = []

        # Apply pattern matching
        for pattern in self.learned_patterns.values():
            if pattern.confidence > 0.7:
                # Check if pattern applies to new conversation
                for insight in new_intelligence.insight_patterns:
                    if pattern.pattern_type == insight.pattern_type:
                        applications.append(
                            f"Applied learned pattern '{pattern.pattern_type}' with confidence {pattern.confidence}"
                        )
                        pattern.application_count += 1

        # Apply capability enhancements
        for capability in self.capabilities.values():
            if capability.effectiveness_score > 0.8:
                applications.append(
                    f"Enhanced analysis using '{capability.capability_name}' capability"
                )

        return applications
