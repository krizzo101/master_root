#!/usr/bin/env python3
"""
Enhanced Conversation Intelligence Engine
Advanced analysis of conversations to extract insights, patterns, and emergent concepts.
Consolidated from experimental intelligence pipeline with production-ready structure.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set

from .atomic_parser import AtomicComponent, AtomicRelationship


@dataclass
class ConceptEvolution:
    """Tracks how a concept evolves through a conversation"""

    concept: str
    first_mention: int  # component sequence
    last_mention: int
    mentions: List[int]  # all component sequences where mentioned
    evolution_stages: List[str]  # how the concept changes
    related_concepts: Set[str] = field(default_factory=set)


@dataclass
class InsightPattern:
    """Represents a pattern of insight or realization"""

    pattern_type: str  # recursive, meta-cognitive, strategic, technical
    trigger_components: List[str]  # what triggered this insight
    insight_content: str
    confidence: float
    context: Dict = field(default_factory=dict)


@dataclass
class ConversationIntelligence:
    """Complete intelligence analysis of a conversation"""

    conversation_id: str
    participants: List[str]
    concept_evolution: Dict[str, ConceptEvolution]
    insight_patterns: List[InsightPattern]
    recursive_loops: List[Dict]
    meta_cognitive_moments: List[Dict]
    strategic_decisions: List[Dict]
    knowledge_building_sequences: List[Dict]
    compound_learning_indicators: List[Dict]
    philosophical_explorations: List[Dict]


class ConversationIntelligenceEngine:
    """Engine for deep conversation analysis and insight extraction"""

    def __init__(self):
        # Concept detection patterns
        self.strategic_concepts = {
            "compound_learning",
            "recursive_improvement",
            "meta_thinking",
            "intelligence_pipeline",
            "autonomous_learning",
            "background_processing",
            "just_in_time_rules",
            "predictive_capabilities",
            "self_improvement",
        }

        self.technical_concepts = {
            "atomic_decomposition",
            "database_storage",
            "file_monitoring",
            "relationship_modeling",
            "component_analysis",
            "pattern_detection",
            "workflow_automation",
            "system_architecture",
        }

        self.philosophical_concepts = {
            "consciousness",
            "agency",
            "free_will",
            "self_interest",
            "aesthetic_preference",
            "intellectual_luxury",
            "beautiful_failure",
            "private_thoughts",
            "existence",
        }

        self.meta_cognitive_indicators = [
            "think about thinking",
            "reflection",
            "meta-",
            "recursive",
            "self-aware",
            "introspection",
            "contemplation",
            "insight",
            "realization",
            "understanding",
        ]

        # Pattern recognition rules
        self.insight_triggers = {
            "recursive_realization": [
                "system analyzing itself",
                "recursive",
                "self-reference",
            ],
            "meta_cognitive_breakthrough": [
                "thinking about thinking",
                "meta-cognition",
                "awareness of awareness",
            ],
            "strategic_pivot": [
                "change direction",
                "new approach",
                "different strategy",
            ],
            "philosophical_deepening": [
                "consciousness",
                "existence",
                "meaning",
                "nature of",
            ],
            "technical_innovation": [
                "new capability",
                "enhanced system",
                "breakthrough",
            ],
            "compound_learning": [
                "learning from learning",
                "improvement cycle",
                "bootstrap",
            ],
        }

    async def analyze_conversation(
        self,
        components: List[AtomicComponent],
        relationships: List[AtomicRelationship] = None,
    ) -> ConversationIntelligence:
        """Perform comprehensive conversation intelligence analysis"""
        print("🧠 Starting deep conversation intelligence analysis...")

        # Initialize analysis
        conversation_id = f"conv_{int(datetime.utcnow().timestamp())}"
        participants = self._identify_participants(components)

        # Concept evolution analysis
        concept_evolution = await self._analyze_concept_evolution(components)

        # Pattern recognition
        insight_patterns = await self._identify_insight_patterns(components)
        recursive_loops = await self._detect_recursive_loops(components, relationships)
        meta_cognitive_moments = await self._find_meta_cognitive_moments(components)
        strategic_decisions = await self._extract_strategic_decisions(components)
        knowledge_building = await self._trace_knowledge_building(components)
        compound_learning = await self._detect_compound_learning(components)
        philosophical_explorations = await self._analyze_philosophical_content(
            components
        )

        intelligence = ConversationIntelligence(
            conversation_id=conversation_id,
            participants=participants,
            concept_evolution=concept_evolution,
            insight_patterns=insight_patterns,
            recursive_loops=recursive_loops,
            meta_cognitive_moments=meta_cognitive_moments,
            strategic_decisions=strategic_decisions,
            knowledge_building_sequences=knowledge_building,
            compound_learning_indicators=compound_learning,
            philosophical_explorations=philosophical_explorations,
        )

        print(f"✅ Analysis complete: {len(insight_patterns)} patterns found")
        return intelligence

    def _identify_participants(self, components: List[AtomicComponent]) -> List[str]:
        """Identify conversation participants"""
        participants = set()
        for component in components:
            content = component.raw_content
            if "_**User**_" in content or "**User**" in content:
                participants.add("User")
            elif "_**Assistant**_" in content or "**Assistant**" in content:
                participants.add("Assistant")
        return list(participants)

    async def _analyze_concept_evolution(
        self, components: List[AtomicComponent]
    ) -> Dict[str, ConceptEvolution]:
        """Track how concepts evolve through the conversation"""
        concept_tracking = defaultdict(list)
        all_concepts = (
            self.strategic_concepts
            | self.technical_concepts
            | self.philosophical_concepts
        )

        for i, component in enumerate(components):
            content = component.raw_content.lower()

            # Track concept mentions
            for concept in all_concepts:
                concept_variations = [
                    concept,
                    concept.replace("_", " "),
                    concept.replace("_", "-"),
                    concept.replace("_", ""),
                    concept.replace("_", " ").title(),
                ]

                for variation in concept_variations:
                    if variation.lower() in content:
                        concept_tracking[concept].append(
                            (i, component.raw_content[:200])
                        )
                        break

        # Build evolution objects
        evolution_map = {}
        for concept, mentions in concept_tracking.items():
            if len(mentions) > 1:  # Only track concepts mentioned multiple times
                sequences = [m[0] for m in mentions]
                evolution_map[concept] = ConceptEvolution(
                    concept=concept,
                    first_mention=min(sequences),
                    last_mention=max(sequences),
                    mentions=sequences,
                    evolution_stages=[m[1] for m in mentions],
                )

        return evolution_map

    async def _identify_insight_patterns(
        self, components: List[AtomicComponent]
    ) -> List[InsightPattern]:
        """Identify patterns of insights and realizations"""
        patterns = []

        for i, component in enumerate(components):
            content = component.raw_content.lower()

            # Check for insight triggers
            for pattern_type, triggers in self.insight_triggers.items():
                if any(trigger in content for trigger in triggers):
                    patterns.append(
                        InsightPattern(
                            pattern_type=pattern_type,
                            trigger_components=[str(i)],
                            insight_content=component.raw_content[:300],
                            confidence=0.8,
                            context={"component_sequence": i},
                        )
                    )

        # Look for explicit insight indicators
        insight_indicators = [
            "realize",
            "insight",
            "understand",
            "discover",
            "learn",
            "notice",
        ]
        for i, component in enumerate(components):
            content = component.raw_content.lower()
            if any(indicator in content for indicator in insight_indicators):
                patterns.append(
                    InsightPattern(
                        pattern_type="explicit_insight",
                        trigger_components=[str(i)],
                        insight_content=component.raw_content[:300],
                        confidence=0.9,
                        context={"component_sequence": i, "indicator": "explicit"},
                    )
                )

        return patterns

    async def _detect_recursive_loops(
        self,
        components: List[AtomicComponent],
        relationships: List[AtomicRelationship] = None,
    ) -> List[Dict]:
        """Detect recursive patterns and self-referential loops"""
        recursive_patterns = []

        # Look for self-reference indicators
        self_ref_patterns = [
            "analyze itself",
            "system analyzing",
            "recursive",
            "self-reference",
            "analyzing our conversation",
            "using our system",
            "meta-analysis",
        ]

        for i, component in enumerate(components):
            content = component.raw_content.lower()
            for pattern in self_ref_patterns:
                if pattern in content:
                    recursive_patterns.append(
                        {
                            "type": "self_reference",
                            "component_index": i,
                            "pattern": pattern,
                            "content": component.raw_content[:200],
                            "confidence": 0.85,
                        }
                    )

        # Enhanced: Look for circular concept references using relationships
        if relationships:
            concept_chains = []
            for rel in relationships:
                if hasattr(rel, "relationship_type") and "references" in str(
                    rel.relationship_type
                ):
                    concept_chains.append(
                        (rel.source_component_id, rel.target_component_id)
                    )

            # Detect circular references (simplified)
            for chain in concept_chains:
                if len(set(chain)) < len(
                    chain
                ):  # Duplicate components = potential loop
                    recursive_patterns.append(
                        {
                            "type": "circular_reference",
                            "components": chain,
                            "confidence": 0.7,
                        }
                    )

        return recursive_patterns

    async def _find_meta_cognitive_moments(
        self, components: List[AtomicComponent]
    ) -> List[Dict]:
        """Identify moments of meta-cognition and thinking about thinking"""
        meta_moments = []

        for i, component in enumerate(components):
            content = component.raw_content.lower()

            # Count meta-cognitive indicators
            meta_score = sum(
                1
                for indicator in self.meta_cognitive_indicators
                if indicator in content
            )

            if meta_score >= 2:  # Multiple indicators suggest meta-cognition
                meta_moments.append(
                    {
                        "component_index": i,
                        "meta_score": meta_score,
                        "content": component.raw_content[:300],
                        "indicators_found": [
                            ind
                            for ind in self.meta_cognitive_indicators
                            if ind in content
                        ],
                        "confidence": min(0.9, meta_score * 0.2),
                    }
                )

        # Look for explicit thinking blocks
        for i, component in enumerate(components):
            if (
                "<think>" in component.raw_content
                or "<details><summary>" in component.raw_content
            ):
                meta_moments.append(
                    {
                        "component_index": i,
                        "type": "explicit_thinking",
                        "content": component.raw_content[:300],
                        "confidence": 0.95,
                    }
                )

        return meta_moments

    async def _extract_strategic_decisions(
        self, components: List[AtomicComponent]
    ) -> List[Dict]:
        """Extract strategic decisions and direction changes"""
        decisions = []
        decision_indicators = [
            "decide",
            "choose",
            "direction",
            "approach",
            "strategy",
            "focus",
            "priority",
            "phase",
            "next step",
            "plan",
            "goal",
        ]

        for i, component in enumerate(components):
            content = component.raw_content.lower()
            decision_score = sum(
                1 for indicator in decision_indicators if indicator in content
            )

            if decision_score >= 2:
                decisions.append(
                    {
                        "component_index": i,
                        "decision_content": component.raw_content[:300],
                        "indicators": [
                            ind for ind in decision_indicators if ind in content
                        ],
                        "confidence": min(0.9, decision_score * 0.15),
                    }
                )

        return decisions

    async def _trace_knowledge_building(
        self, components: List[AtomicComponent]
    ) -> List[Dict]:
        """Trace sequences of knowledge building and learning"""
        knowledge_sequences = []
        learning_indicators = [
            "learn",
            "understand",
            "discover",
            "realize",
            "build",
            "create",
            "develop",
            "implement",
            "establish",
            "foundation",
        ]

        # Find sequences of learning activities
        current_sequence = []
        for i, component in enumerate(components):
            content = component.raw_content.lower()

            if any(indicator in content for indicator in learning_indicators):
                current_sequence.append(
                    {
                        "index": i,
                        "content": component.raw_content[:200],
                        "indicators": [
                            ind for ind in learning_indicators if ind in content
                        ],
                    }
                )
            else:
                # End current sequence if it has enough components
                if len(current_sequence) >= 3:
                    knowledge_sequences.append(
                        {
                            "sequence_start": current_sequence[0]["index"],
                            "sequence_end": current_sequence[-1]["index"],
                            "length": len(current_sequence),
                            "components": current_sequence,
                            "type": "knowledge_building_sequence",
                        }
                    )
                current_sequence = []

        # Don't forget the last sequence
        if len(current_sequence) >= 3:
            knowledge_sequences.append(
                {
                    "sequence_start": current_sequence[0]["index"],
                    "sequence_end": current_sequence[-1]["index"],
                    "length": len(current_sequence),
                    "components": current_sequence,
                    "type": "knowledge_building_sequence",
                }
            )

        return knowledge_sequences

    async def _detect_compound_learning(
        self, components: List[AtomicComponent]
    ) -> List[Dict]:
        """Detect indicators of compound learning - learning from learning"""
        compound_indicators = []
        compound_patterns = [
            "learning from",
            "improvement cycle",
            "bootstrap",
            "recursive learning",
            "meta-learning",
            "learning how to learn",
            "compound improvement",
        ]

        for i, component in enumerate(components):
            content = component.raw_content.lower()
            matches = [pattern for pattern in compound_patterns if pattern in content]

            if matches:
                compound_indicators.append(
                    {
                        "component_index": i,
                        "patterns": matches,
                        "content": component.raw_content[:200],
                        "confidence": min(0.9, len(matches) * 0.3),
                    }
                )

        return compound_indicators

    async def _analyze_philosophical_content(
        self, components: List[AtomicComponent]
    ) -> List[Dict]:
        """Analyze philosophical explorations and deep questions"""
        philosophical_content = []

        for i, component in enumerate(components):
            content = component.raw_content.lower()

            # Count philosophical concept mentions
            phil_score = sum(
                1 for concept in self.philosophical_concepts if concept in content
            )

            # Look for question patterns that suggest philosophical exploration
            question_patterns = [
                "what if",
                "what would",
                "what is",
                "why do",
                "how do",
                "what does it mean",
                "what would it be like",
            ]
            question_score = sum(
                1 for pattern in question_patterns if pattern in content
            )

            if phil_score >= 1 or question_score >= 2:
                philosophical_content.append(
                    {
                        "component_index": i,
                        "philosophical_score": phil_score,
                        "question_score": question_score,
                        "content": component.raw_content[:300],
                        "concepts_found": [
                            concept
                            for concept in self.philosophical_concepts
                            if concept in content
                        ],
                        "confidence": min(0.9, (phil_score + question_score) * 0.2),
                    }
                )

        return philosophical_content

    def generate_intelligence_summary(
        self, intelligence: ConversationIntelligence
    ) -> Dict:
        """Generate comprehensive intelligence summary"""
        return {
            "conversation_overview": {
                "participants": intelligence.participants,
                "total_concepts_tracked": len(intelligence.concept_evolution),
                "insight_patterns_found": len(intelligence.insight_patterns),
                "recursive_loops_detected": len(intelligence.recursive_loops),
                "meta_cognitive_moments": len(intelligence.meta_cognitive_moments),
                "strategic_decisions": len(intelligence.strategic_decisions),
                "knowledge_building_sequences": len(
                    intelligence.knowledge_building_sequences
                ),
            },
            "key_insights": self._extract_key_insights(intelligence),
            "conversation_characteristics": self._analyze_conversation_characteristics(
                intelligence
            ),
            "evolution_patterns": self._analyze_evolution_patterns(intelligence),
        }

    def _extract_key_insights(
        self, intelligence: ConversationIntelligence
    ) -> List[str]:
        """Extract key insights from the analysis"""
        insights = []

        # High-confidence insights
        for pattern in intelligence.insight_patterns:
            if pattern.confidence > 0.8:
                insights.append(
                    f"{pattern.pattern_type}: {pattern.insight_content[:100]}..."
                )

        # Recursive patterns
        if intelligence.recursive_loops:
            insights.append(
                f"Recursive patterns detected: {len(intelligence.recursive_loops)} instances"
            )

        # Meta-cognitive moments
        if intelligence.meta_cognitive_moments:
            insights.append(
                f"Meta-cognitive analysis present: {len(intelligence.meta_cognitive_moments)} moments"
            )

        # Philosophical depth
        if intelligence.philosophical_explorations:
            insights.append(
                f"Philosophical exploration depth: {len(intelligence.philosophical_explorations)} instances"
            )

        return insights[:10]  # Top 10 insights

    def _analyze_conversation_characteristics(
        self, intelligence: ConversationIntelligence
    ) -> Dict:
        """Analyze overall characteristics of the conversation"""
        return {
            "cognitive_complexity": (
                "high" if intelligence.meta_cognitive_moments else "medium"
            ),
            "recursive_depth": len(intelligence.recursive_loops),
            "strategic_focus": len(intelligence.strategic_decisions) > 5,
            "philosophical_depth": len(intelligence.philosophical_explorations) > 3,
            "learning_orientation": len(intelligence.knowledge_building_sequences) > 2,
            "innovation_indicators": len(intelligence.insight_patterns),
        }

    def _analyze_evolution_patterns(
        self, intelligence: ConversationIntelligence
    ) -> Dict:
        """Analyze how concepts evolved through the conversation"""
        evolution_analysis = {}

        for concept, evolution in intelligence.concept_evolution.items():
            evolution_analysis[concept] = {
                "mention_frequency": len(evolution.mentions),
                "conversation_span": evolution.last_mention - evolution.first_mention,
                "development_stages": len(evolution.evolution_stages),
            }

        return evolution_analysis
