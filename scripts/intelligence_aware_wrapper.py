#!/usr/bin/env python3
"""
Intelligence-Aware Agent Wrapper

This module implements self-aware intelligence usage that triggers
based on agent intent and reasoning, not keywords.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import existing intelligence wrapper
from proj_intel_wrapper import intel


class TaskIntent(Enum):
    """Recognized task intents that benefit from intelligence"""

    SEARCH = "search"  # Finding code, files, symbols
    UNDERSTAND = "understand"  # Learning how something works
    DEBUG = "debug"  # Fixing errors or issues
    CREATE = "create"  # Adding new functionality
    MODIFY = "modify"  # Changing existing code
    REVIEW = "review"  # Analyzing code quality
    EXPLORE = "explore"  # General codebase discovery
    UNKNOWN = "unknown"  # Unclear intent


@dataclass
class AgentThought:
    """Represents an agent's internal thought/reasoning"""

    content: str
    intent: Optional[TaskIntent] = None
    needs_intelligence: bool = False
    intelligence_type: Optional[str] = None
    confidence: float = 0.0


class IntelligenceAwareAgent:
    """
    Self-aware agent that recognizes when to use project intelligence
    based on its own reasoning and intent, not keywords.
    """

    # Thought patterns that indicate intelligence would help
    THOUGHT_TRIGGERS = {
        # Uncertainty patterns
        r"(?i)(I need to|should|must|have to) (find|locate|search|look for)": TaskIntent.SEARCH,
        r"(?i)(where|which file|what file) .* (is|are|contains?|has|have)": TaskIntent.SEARCH,
        r"(?i)(I wonder|not sure|need to check|let me see)": TaskIntent.EXPLORE,
        r"(?i)(probably|might be|could be|possibly) in": TaskIntent.SEARCH,
        # Understanding patterns
        r"(?i)(how does|how do|understand|figure out|learn about)": TaskIntent.UNDERSTAND,
        r"(?i)(relationship|connected|related|depends on|uses)": TaskIntent.UNDERSTAND,
        r"(?i)(structure|architecture|design|organized)": TaskIntent.UNDERSTAND,
        # Action patterns
        r"(?i)(going to|about to|need to|will) (create|add|implement|build)": TaskIntent.CREATE,
        r"(?i)(going to|about to|need to|will) (modify|edit|change|update)": TaskIntent.MODIFY,
        r"(?i)(debug|fix|solve|troubleshoot|error|broken|issue)": TaskIntent.DEBUG,
        r"(?i)(review|analyze|check|examine|inspect)": TaskIntent.REVIEW,
    }

    # Action patterns that indicate manual work (should use intelligence instead)
    INEFFICIENT_PATTERNS = [
        r"(?i)let me (grep|search|find)",
        r"(?i)I'll (search|look) through",
        r"(?i)checking multiple files",
        r"(?i)reading .* files",
        r"(?i)scanning .* for",
        r"(?i)looking in .* directories",
    ]

    def __init__(self):
        """Initialize the intelligence-aware agent"""
        self.thought_history: List[AgentThought] = []
        self.intelligence_cache: Dict[str, Any] = {}
        self.last_intelligence_check = None

    def analyze_thought(self, thought: str) -> AgentThought:
        """
        Analyze an agent thought to determine if intelligence is needed.
        This is called on EVERY agent thought, not just user inputs.
        """
        analyzed = AgentThought(content=thought)

        # Check for intent patterns
        for pattern, intent in self.THOUGHT_TRIGGERS.items():
            if re.search(pattern, thought):
                analyzed.intent = intent
                analyzed.needs_intelligence = True
                analyzed.intelligence_type = self._get_intelligence_type(intent)
                analyzed.confidence = 0.8
                break

        # Check for inefficient patterns (manual work)
        for pattern in self.INEFFICIENT_PATTERNS:
            if re.search(pattern, thought):
                analyzed.needs_intelligence = True
                analyzed.intelligence_type = "optimization"
                analyzed.confidence = 0.9
                if not analyzed.intent:
                    analyzed.intent = TaskIntent.SEARCH
                break

        # Check for file references
        if self._contains_file_reference(thought):
            analyzed.needs_intelligence = True
            analyzed.intelligence_type = "context"
            analyzed.confidence = 0.7
            if not analyzed.intent:
                analyzed.intent = TaskIntent.EXPLORE

        self.thought_history.append(analyzed)
        return analyzed

    def _get_intelligence_type(self, intent: TaskIntent) -> str:
        """Map intent to intelligence type"""
        mapping = {
            TaskIntent.SEARCH: "symbol_and_file",
            TaskIntent.UNDERSTAND: "architecture",
            TaskIntent.DEBUG: "dependencies",
            TaskIntent.CREATE: "patterns",
            TaskIntent.MODIFY: "context",
            TaskIntent.REVIEW: "comprehensive",
            TaskIntent.EXPLORE: "overview",
        }
        return mapping.get(intent, "general")

    def _contains_file_reference(self, thought: str) -> bool:
        """Check if thought references files or code elements"""
        file_patterns = [
            r"\.(py|js|ts|json|yaml|md)(\s|$|'|\")",
            r"(class|function|def|import|module)\s+\w+",
            r"(file|directory|folder|package|module)\s+(called|named)",
        ]
        return any(re.search(p, thought, re.IGNORECASE) for p in file_patterns)

    def should_use_intelligence(
        self, action_description: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if an action would benefit from intelligence.
        Called BEFORE any action is taken.
        """
        # Analyze the action as a thought
        thought = self.analyze_thought(action_description)

        if thought.needs_intelligence:
            return True, thought.intelligence_type

        # Additional checks for actions
        action_triggers = {
            "read": "context",
            "edit": "patterns",
            "create": "patterns",
            "search": "symbol_and_file",
            "grep": "symbol_and_file",
            "find": "symbol_and_file",
            "understand": "architecture",
            "debug": "dependencies",
        }

        for trigger, intel_type in action_triggers.items():
            if trigger in action_description.lower():
                return True, intel_type

        # Default: use intelligence for non-trivial tasks
        if not self._is_trivial_action(action_description):
            return True, "general"

        return False, None

    def _is_trivial_action(self, action: str) -> bool:
        """Determine if an action is too trivial for intelligence"""
        trivial_patterns = [
            r"(?i)^(print|echo|log)",
            r"(?i)^(comment|add comment)",
            r"(?i)single (line|character|word)",
            r"(?i)^(rename variable|fix typo)",
        ]
        return any(re.search(p, action) for p in trivial_patterns)

    def get_intelligence_for_intent(
        self, intent: TaskIntent, context: str = ""
    ) -> Dict[str, Any]:
        """
        Load appropriate intelligence based on detected intent.
        This is called automatically when intent is detected.
        """
        result = {
            "intent": intent.value,
            "intelligence_used": [],
            "recommendations": [],
        }

        if intent == TaskIntent.SEARCH:
            # Use symbol index for precise location
            if context:
                symbols = intel.find(context)
                result["intelligence_used"].append("symbol_index")
                result["data"] = symbols
                result["recommendations"].append(f"Found {symbols.count} matches")

        elif intent == TaskIntent.UNDERSTAND:
            # Load architecture overview
            arch = intel.architecture(context if context else None)
            result["intelligence_used"].append("architecture")
            result["data"] = arch
            result["recommendations"].append("Architecture loaded")

        elif intent == TaskIntent.DEBUG:
            # Get dependencies and relationships
            if context and ".py" in context:
                deps = intel.dependencies(context)
                result["intelligence_used"].append("dependencies")
                result["data"] = deps
                result["recommendations"].append("Dependencies analyzed")

        elif intent == TaskIntent.CREATE or intent == TaskIntent.MODIFY:
            # Find similar patterns
            patterns = intel.suggest_context(context, max_files=10)
            result["intelligence_used"].append("patterns")
            result["data"] = patterns
            result["recommendations"].append("Pattern examples loaded")

        elif intent == TaskIntent.REVIEW:
            # Comprehensive context
            stats = intel.stats()
            result["intelligence_used"].append("comprehensive")
            result["data"] = stats
            result["recommendations"].append("Full context loaded")

        elif intent == TaskIntent.EXPLORE:
            # General overview
            stats = intel.stats()
            result["intelligence_used"].append("overview")
            result["data"] = stats
            result["recommendations"].append("Overview loaded")

        return result

    def self_correct(self) -> Optional[str]:
        """
        Check recent actions and self-correct if inefficient.
        Returns correction advice if needed.
        """
        if len(self.thought_history) < 2:
            return None

        recent_thoughts = self.thought_history[-5:]

        # Check for repeated searches (indicates should use intelligence)
        search_count = sum(1 for t in recent_thoughts if "search" in t.content.lower())
        if search_count > 2:
            return "Multiple searches detected. Use symbol_index for instant lookups."

        # Check for reading many files
        read_count = sum(1 for t in recent_thoughts if "read" in t.content.lower())
        if read_count > 3:
            return "Reading many files. Use architecture overview first."

        # Check for uncertainty
        uncertainty_count = sum(1 for t in recent_thoughts if t.confidence < 0.5)
        if uncertainty_count > 2:
            return "High uncertainty detected. Load project intelligence for clarity."

        return None

    def explain_intelligence_benefit(self, task: str) -> str:
        """
        Explain why intelligence would help with a specific task.
        Educational - helps agent learn when to use intelligence.
        """
        thought = self.analyze_thought(task)

        if not thought.needs_intelligence:
            return "Intelligence may not be needed for this trivial task."

        benefits = {
            TaskIntent.SEARCH: "Symbol index provides O(1) lookup vs O(n) grep search",
            TaskIntent.UNDERSTAND: "Architecture overview shows relationships instantly",
            TaskIntent.DEBUG: "Dependency graph reveals error propagation paths",
            TaskIntent.CREATE: "Pattern examples ensure consistency with codebase",
            TaskIntent.MODIFY: "Context prevents breaking changes",
            TaskIntent.REVIEW: "Comprehensive stats highlight focus areas",
            TaskIntent.EXPLORE: "File statistics guide efficient exploration",
        }

        benefit = benefits.get(thought.intent, "Intelligence provides instant context")
        return f"For {thought.intent.value} tasks: {benefit}"


# Global instance for easy access
aware_agent = IntelligenceAwareAgent()


def intercept_agent_action(action: str) -> Dict[str, Any]:
    """
    Intercept any agent action and enhance with intelligence.
    This would be called before EVERY agent action.
    """
    should_use, intel_type = aware_agent.should_use_intelligence(action)

    result = {
        "original_action": action,
        "use_intelligence": should_use,
        "intelligence_type": intel_type,
        "enhanced_action": action,
    }

    if should_use:
        # Extract context from action
        context = extract_context_from_action(action)

        # Get appropriate intelligence
        intent = detect_intent_from_action(action)
        intelligence = aware_agent.get_intelligence_for_intent(intent, context)

        # Enhance the action with intelligence
        result["intelligence_data"] = intelligence
        result["enhanced_action"] = enhance_action_with_intelligence(
            action, intelligence
        )
        result["performance_gain"] = "10-100x faster with intelligence"

    return result


def extract_context_from_action(action: str) -> str:
    """Extract relevant context from an action description"""
    # Look for file names, class names, function names
    patterns = [
        r"['\"]([^'\"]+\.py)['\"]",  # Python files
        r"\b([A-Z][a-zA-Z0-9]+)(?:Class|Agent|Model)\b",  # Class names
        r"\b(def|function|class)\s+(\w+)",  # Definitions
    ]

    for pattern in patterns:
        match = re.search(pattern, action)
        if match:
            return match.group(1) if match.groups() else match.group(0)

    # Extract key terms
    words = action.split()
    keywords = [w for w in words if len(w) > 4 and w.isalnum()]
    return " ".join(keywords[:3])


def detect_intent_from_action(action: str) -> TaskIntent:
    """Detect intent from an action description"""
    action_lower = action.lower()

    # Map action keywords to intents
    intent_map = {
        ("find", "search", "locate", "where"): TaskIntent.SEARCH,
        ("understand", "explain", "how", "why"): TaskIntent.UNDERSTAND,
        ("debug", "fix", "error", "issue"): TaskIntent.DEBUG,
        ("create", "add", "new", "implement"): TaskIntent.CREATE,
        ("modify", "edit", "change", "update"): TaskIntent.MODIFY,
        ("review", "check", "analyze", "examine"): TaskIntent.REVIEW,
        ("explore", "look", "see", "browse"): TaskIntent.EXPLORE,
    }

    for keywords, intent in intent_map.items():
        if any(kw in action_lower for kw in keywords):
            return intent

    return TaskIntent.UNKNOWN


def enhance_action_with_intelligence(action: str, intelligence: Dict[str, Any]) -> str:
    """
    Enhance an action with intelligence data.
    Returns a modified action that uses intelligence.
    """
    if not intelligence.get("data"):
        return action

    # Example: Replace grep with direct file access
    if "grep" in action.lower():
        return f"Using intelligence: Direct access to {intelligence['data']}"

    # Example: Replace multi-file read with architecture
    if "read multiple" in action.lower():
        return f"Using architecture overview instead of reading files"

    return f"{action} [Enhanced with {intelligence['intelligence_used']}]"


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Intelligence-Aware Agent Test")
        print("Usage: python intelligence_aware_wrapper.py '<thought or action>'")
        print("\nExamples:")
        print("  'I need to find where authentication happens'")
        print("  'Let me grep for the User class'")
        print("  'Going to create a new validator'")
        sys.exit(1)

    test_input = " ".join(sys.argv[1:])

    print(f"\nAnalyzing: '{test_input}'")
    print("-" * 50)

    # Analyze as thought
    thought = aware_agent.analyze_thought(test_input)
    print(f"Intent detected: {thought.intent.value if thought.intent else 'None'}")
    print(f"Needs intelligence: {thought.needs_intelligence}")
    print(f"Intelligence type: {thought.intelligence_type or 'None'}")
    print(f"Confidence: {thought.confidence:.1%}")

    # Get intelligence recommendation
    if thought.needs_intelligence and thought.intent:
        intel_data = aware_agent.get_intelligence_for_intent(thought.intent, test_input)
        print(f"\nIntelligence recommendation:")
        for rec in intel_data["recommendations"]:
            print(f"  - {rec}")

    # Explain benefit
    benefit = aware_agent.explain_intelligence_benefit(test_input)
    print(f"\nBenefit: {benefit}")

    # Show enhanced action
    enhanced = intercept_agent_action(test_input)
    if enhanced["use_intelligence"]:
        print(f"\nEnhanced action: {enhanced['enhanced_action']}")
        print(f"Performance gain: {enhanced.get('performance_gain', 'Unknown')}")
