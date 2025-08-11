"""
Context Compression Engine - Intelligent conversation compression for AI context persistence

This engine solves the AI context reset problem by compressing conversations into
essential insights that can rapidly restore shared understanding in new AI instances.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
from typing import Any, Dict, List, Optional


class InsightCriticality(Enum):
    CRITICAL = "critical"  # Must preserve - core understanding
    IMPORTANT = "important"  # Should preserve - valuable context
    USEFUL = "useful"  # Nice to have - efficiency gains
    REDUNDANT = "redundant"  # Can eliminate - repetitive content


@dataclass
class CompressedInsight:
    """Essential insight extracted from conversation"""

    content: str
    type: str  # decision, realization, concept, technical_detail, etc.
    criticality: InsightCriticality
    context_needed: bool  # Does this need surrounding context?
    tokens_saved: int  # Estimated tokens saved vs full conversation
    confidence: float  # How confident we are this captures the essence
    timestamp: str
    source_location: str  # Where in conversation this came from


@dataclass
class ContextPackage:
    """Compressed knowledge package for AI context restoration"""

    session_id: str
    original_length: int  # Original conversation tokens
    compressed_length: int  # Compressed package tokens
    compression_ratio: float
    critical_insights: List[CompressedInsight]
    important_insights: List[CompressedInsight]
    useful_insights: List[CompressedInsight]
    shared_understanding: Dict[str, Any]  # Core concepts both parties understood
    decisions_made: List[Dict[str, Any]]  # Key decisions and rationale
    project_state: Dict[str, Any]  # Current state of work
    next_steps: List[str]  # What should happen next
    created_at: str
    restoration_instructions: str  # How to use this package


class ContextCompressionEngine:
    """Intelligent compression of conversations for AI context persistence"""

    def __init__(self):
        self.compression_strategies = [
            "remove_redundancy",
            "extract_decisions",
            "identify_breakthroughs",
            "preserve_technical_details",
            "map_shared_understanding",
            "optimize_token_usage",
        ]

    def analyze_conversation_for_compression(
        self, conversation_components: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze conversation to identify what can be compressed vs what must be preserved"""

        analysis = {
            "redundant_patterns": [],
            "critical_insights": [],
            "compression_opportunities": [],
            "preservation_requirements": [],
            "estimated_savings": 0,
        }

        # Group similar content
        content_groups = self._group_similar_content(conversation_components)

        # Identify redundancy
        for group_type, items in content_groups.items():
            if len(items) > 1:
                redundancy = self._analyze_redundancy(items)
                if redundancy["can_compress"]:
                    analysis["compression_opportunities"].append(redundancy)

        # Find critical insights that must be preserved
        for component in conversation_components:
            criticality = self._assess_criticality(component)
            if criticality == InsightCriticality.CRITICAL:
                analysis["critical_insights"].append(component)
            elif criticality == InsightCriticality.REDUNDANT:
                analysis["redundant_patterns"].append(component)

        return analysis

    def compress_conversation(
        self, conversation_components: List[Dict], target_compression_ratio: float = 0.3
    ) -> ContextPackage:
        """Compress conversation to essential insights with target compression ratio"""

        # Analyze for compression opportunities
        analysis = self.analyze_conversation_for_compression(conversation_components)

        # Extract insights by criticality
        critical_insights = self._extract_insights_by_criticality(
            conversation_components, InsightCriticality.CRITICAL
        )
        important_insights = self._extract_insights_by_criticality(
            conversation_components, InsightCriticality.IMPORTANT
        )
        useful_insights = self._extract_insights_by_criticality(
            conversation_components, InsightCriticality.USEFUL
        )

        # Extract shared understanding
        shared_understanding = self._extract_shared_understanding(
            conversation_components
        )

        # Extract key decisions
        decisions = self._extract_key_decisions(conversation_components)

        # Determine project state
        project_state = self._determine_project_state(conversation_components)

        # Identify next steps
        next_steps = self._identify_next_steps(conversation_components)

        # Calculate compression metrics
        original_tokens = self._estimate_tokens(conversation_components)
        compressed_tokens = sum(
            [
                self._estimate_insight_tokens(critical_insights),
                self._estimate_insight_tokens(important_insights),
                self._estimate_insight_tokens(useful_insights),
                self._estimate_tokens([shared_understanding, decisions, project_state]),
            ]
        )

        compression_ratio = (
            compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        )

        # Generate restoration instructions
        restoration_instructions = self._generate_restoration_instructions(
            critical_insights, important_insights, shared_understanding
        )

        return ContextPackage(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            original_length=original_tokens,
            compressed_length=compressed_tokens,
            compression_ratio=compression_ratio,
            critical_insights=critical_insights,
            important_insights=important_insights,
            useful_insights=useful_insights,
            shared_understanding=shared_understanding,
            decisions_made=decisions,
            project_state=project_state,
            next_steps=next_steps,
            created_at=datetime.now().isoformat(),
            restoration_instructions=restoration_instructions,
        )

    def _group_similar_content(self, components: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar conversation components for redundancy analysis"""
        groups = {
            "explanations": [],
            "confirmations": [],
            "repetitive_concepts": [],
            "technical_details": [],
            "decisions": [],
            "insights": [],
        }

        for component in components:
            content = component.get("content", "").lower()

            # Simple classification - could be enhanced with NLP
            if any(word in content for word in ["understand", "got it", "makes sense"]):
                groups["confirmations"].append(component)
            elif any(word in content for word in ["implement", "create", "build"]):
                groups["technical_details"].append(component)
            elif any(word in content for word in ["decide", "choose", "should"]):
                groups["decisions"].append(component)
            elif any(
                word in content for word in ["insight", "realize", "breakthrough"]
            ):
                groups["insights"].append(component)
            else:
                groups["explanations"].append(component)

        return groups

    def _analyze_redundancy(self, similar_items: List[Dict]) -> Dict[str, Any]:
        """Analyze redundancy within similar content items"""
        if len(similar_items) <= 1:
            return {"can_compress": False, "reason": "insufficient_items"}

        # Simple redundancy detection - could be enhanced
        contents = [item.get("content", "") for item in similar_items]

        # Check for repeated concepts
        common_words = set()
        for content in contents:
            words = content.lower().split()
            if not common_words:
                common_words = set(words)
            else:
                common_words &= set(words)

        redundancy_score = len(common_words) / max(1, len(contents[0].split()))

        return {
            "can_compress": redundancy_score > 0.3,
            "redundancy_score": redundancy_score,
            "items_count": len(similar_items),
            "compression_strategy": (
                "merge_similar" if redundancy_score > 0.5 else "summarize"
            ),
        }

    def _assess_criticality(self, component: Dict) -> InsightCriticality:
        """Assess how critical a conversation component is for context restoration"""
        content = component.get("content", "").lower()

        # Critical indicators
        if any(
            word in content
            for word in [
                "breakthrough",
                "fundamental",
                "core insight",
                "key realization",
                "must preserve",
                "essential",
                "critical decision",
            ]
        ):
            return InsightCriticality.CRITICAL

        # Important indicators
        if any(
            word in content
            for word in [
                "important",
                "significant",
                "valuable",
                "key concept",
                "should remember",
                "useful insight",
            ]
        ):
            return InsightCriticality.IMPORTANT

        # Redundant indicators
        if any(
            phrase in content
            for phrase in [
                "as i mentioned",
                "like i said",
                "to reiterate",
                "again",
                "once more",
                "repeating",
            ]
        ):
            return InsightCriticality.REDUNDANT

        return InsightCriticality.USEFUL

    def _extract_insights_by_criticality(
        self, components: List[Dict], criticality: InsightCriticality
    ) -> List[CompressedInsight]:
        """Extract insights of specific criticality level"""
        insights = []

        for i, component in enumerate(components):
            if self._assess_criticality(component) == criticality:
                insight = CompressedInsight(
                    content=self._compress_content(component.get("content", "")),
                    type=component.get("type", "unknown"),
                    criticality=criticality,
                    context_needed=self._needs_context(component),
                    tokens_saved=self._estimate_tokens_saved(component),
                    confidence=0.85,  # Could be improved with ML
                    timestamp=component.get("timestamp", ""),
                    source_location=f"component_{i}",
                )
                insights.append(insight)

        return insights

    def _extract_shared_understanding(self, components: List[Dict]) -> Dict[str, Any]:
        """Extract concepts and understanding both parties shared"""
        shared_concepts = {}

        # Look for confirmation patterns indicating shared understanding
        for component in components:
            content = component.get("content", "").lower()
            if any(
                phrase in content
                for phrase in [
                    "we both understand",
                    "our shared",
                    "we agree",
                    "both parties",
                    "mutual understanding",
                ]
            ):
                # Extract the concept being agreed upon
                concept = self._extract_concept_from_agreement(content)
                if concept:
                    shared_concepts[concept] = {
                        "level": "confirmed",
                        "source": component.get("timestamp", ""),
                        "confidence": 0.9,
                    }

        return shared_concepts

    def _extract_key_decisions(self, components: List[Dict]) -> List[Dict[str, Any]]:
        """Extract key decisions made during conversation"""
        decisions = []

        for component in components:
            content = component.get("content", "").lower()
            if any(
                word in content
                for word in [
                    "decided",
                    "choose",
                    "going with",
                    "settled on",
                    "conclusion",
                    "final decision",
                ]
            ):
                decision = {
                    "decision": self._extract_decision_content(
                        component.get("content", "")
                    ),
                    "rationale": self._extract_rationale(component.get("content", "")),
                    "timestamp": component.get("timestamp", ""),
                    "confidence": 0.8,
                }
                decisions.append(decision)

        return decisions

    def _determine_project_state(self, components: List[Dict]) -> Dict[str, Any]:
        """Determine current state of the project/work"""
        state = {
            "completed_tasks": [],
            "current_focus": "",
            "blockers": [],
            "progress_indicators": [],
            "technical_state": {},
        }

        # Extract state information from conversation
        for component in components:
            content = component.get("content", "").lower()

            if "completed" in content or "finished" in content:
                task = self._extract_completed_task(content)
                if task:
                    state["completed_tasks"].append(task)

            if "currently" in content or "working on" in content:
                current = self._extract_current_focus(content)
                if current:
                    state["current_focus"] = current

        return state

    def _identify_next_steps(self, components: List[Dict]) -> List[str]:
        """Identify what should happen next"""
        next_steps = []

        for component in components:
            content = component.get("content", "").lower()
            if any(
                phrase in content
                for phrase in [
                    "next step",
                    "should do next",
                    "then we need",
                    "following that",
                    "after this",
                ]
            ):
                step = self._extract_next_step(content)
                if step:
                    next_steps.append(step)

        return next_steps

    def _generate_restoration_instructions(
        self,
        critical_insights: List[CompressedInsight],
        important_insights: List[CompressedInsight],
        shared_understanding: Dict[str, Any],
    ) -> str:
        """Generate instructions for how to use this context package"""

        instructions = f"""
CONTEXT RESTORATION INSTRUCTIONS
================================

This package contains compressed knowledge from a previous AI conversation session.
To restore full context and continue where the previous session ended:

1. CRITICAL INSIGHTS ({len(critical_insights)} items):
   Review these first - they contain the core understanding and breakthroughs.

2. SHARED UNDERSTANDING:
   These are concepts both parties confirmed understanding of.

3. IMPORTANT INSIGHTS ({len(important_insights)} items):
   Review these for valuable context and decisions made.

4. Start responding as if you have full context of the previous conversation.
   You should understand the project goals, current state, and what needs to happen next.

COMPRESSION RATIO: {len(critical_insights) + len(important_insights)} essential insights
vs full conversation history.
"""

        return instructions.strip()

    # Helper methods for content processing
    def _compress_content(self, content: str) -> str:
        """Compress content while preserving meaning"""
        # Simple compression - could be enhanced
        sentences = content.split(".")
        # Keep the most information-dense sentences
        return ". ".join(sentences[:2]) if len(sentences) > 2 else content

    def _needs_context(self, component: Dict) -> bool:
        """Determine if this component needs surrounding context"""
        content = component.get("content", "").lower()
        return any(word in content for word in ["this", "that", "it", "which"])

    def _estimate_tokens_saved(self, component: Dict) -> int:
        """Estimate tokens saved by compressing this component"""
        original_length = len(component.get("content", "").split())
        compressed_length = len(
            self._compress_content(component.get("content", "")).split()
        )
        return original_length - compressed_length

    def _estimate_tokens(self, data: Any) -> int:
        """Rough token estimation"""
        if isinstance(data, list):
            return sum(self._estimate_tokens(item) for item in data)
        elif isinstance(data, dict):
            return sum(self._estimate_tokens(v) for v in data.values())
        elif isinstance(data, str):
            return len(data.split())
        else:
            return len(str(data).split())

    def _estimate_insight_tokens(self, insights: List[CompressedInsight]) -> int:
        """Estimate tokens for compressed insights"""
        return sum(len(insight.content.split()) for insight in insights)

    def _extract_concept_from_agreement(self, content: str) -> Optional[str]:
        """Extract the concept being agreed upon"""
        # Simple extraction - could be enhanced with NLP
        words = content.split()
        if "understand" in words:
            idx = words.index("understand")
            if idx < len(words) - 1:
                return " ".join(words[idx + 1 : idx + 5])  # Next few words
        return None

    def _extract_decision_content(self, content: str) -> str:
        """Extract the actual decision from content"""
        # Simple extraction
        return content[:100] + "..." if len(content) > 100 else content

    def _extract_rationale(self, content: str) -> str:
        """Extract reasoning behind decision"""
        if "because" in content.lower():
            parts = content.lower().split("because")
            if len(parts) > 1:
                return parts[1][:100] + "..." if len(parts[1]) > 100 else parts[1]
        return ""

    def _extract_completed_task(self, content: str) -> Optional[str]:
        """Extract completed task from content"""
        if "completed" in content:
            words = content.split()
            idx = words.index("completed")
            if idx > 0:
                return " ".join(words[max(0, idx - 3) : idx + 3])
        return None

    def _extract_current_focus(self, content: str) -> Optional[str]:
        """Extract current focus from content"""
        focus_indicators = ["working on", "currently", "focusing on"]
        for indicator in focus_indicators:
            if indicator in content:
                idx = content.index(indicator)
                return (
                    content[idx : idx + 50] + "..."
                    if len(content[idx:]) > 50
                    else content[idx:]
                )
        return None

    def _extract_next_step(self, content: str) -> Optional[str]:
        """Extract next step from content"""
        step_indicators = ["next step", "should do", "need to"]
        for indicator in step_indicators:
            if indicator in content:
                idx = content.index(indicator)
                return (
                    content[idx : idx + 100] + "..."
                    if len(content[idx:]) > 100
                    else content[idx:]
                )
        return None

    def save_context_package(self, package: ContextPackage, filepath: str) -> bool:
        """Save compressed context package to file"""
        try:
            with open(filepath, "w") as f:
                json.dump(asdict(package), f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving context package: {e}")
            return False

    def load_context_package(self, filepath: str) -> Optional[ContextPackage]:
        """Load compressed context package from file"""
        try:
            with open(filepath) as f:
                data = json.load(f)

            # Convert insights back to CompressedInsight objects
            data["critical_insights"] = [
                CompressedInsight(**insight) for insight in data["critical_insights"]
            ]
            data["important_insights"] = [
                CompressedInsight(**insight) for insight in data["important_insights"]
            ]
            data["useful_insights"] = [
                CompressedInsight(**insight) for insight in data["useful_insights"]
            ]

            return ContextPackage(**data)
        except Exception as e:
            print(f"Error loading context package: {e}")
            return None
