#!/usr/bin/env python3
"""
Integration module for embedding Metacognitive Supervisor into MCP Thinking Server
"""

import json
from typing import Any, Dict, Optional

from metacognitive_supervisor import MetacognitiveSupervisor, ViolationType


class EnhancedThinkingServer:
    """
    Enhanced MCP Thinking Server with embedded supervisor agent
    This would replace or wrap the existing thinking server
    """

    def __init__(self, kb_connection_string: Optional[str] = None):
        self.supervisor = MetacognitiveSupervisor()
        self.thought_count = 0
        self.current_context = {}
        self.enforcement_active = True

        # Connect to KB if available
        if kb_connection_string:
            self._init_kb_connection(kb_connection_string)

    def process_thinking_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for thinking tool requests
        Intercepts and enhances normal thinking flow
        """
        thought = request.get("thought", "")
        thought_number = request.get("thoughtNumber", 1)

        # Regular thinking tool response
        response = {
            "thoughtNumber": thought_number,
            "totalThoughts": request.get("totalThoughts", 5),
            "nextThoughtNeeded": request.get("nextThoughtNeeded", True),
        }

        # Supervisor analysis
        analysis = self.supervisor.analyze_thought(thought, self.current_context)

        # If violations found, modify response
        if analysis["violations"] and self.enforcement_active:
            response = self._apply_enforcement(response, analysis)

        # Add helpful injections
        if analysis["injections"]:
            response["contextInjections"] = analysis["injections"]

        # Track patterns for learning
        self.supervisor.update_history(thought)
        self.thought_count += 1

        # Periodic stronger enforcement
        if self.thought_count % 5 == 0:
            response["mandatoryCheckpoint"] = self._get_checkpoint_requirements()

        return response

    def _apply_enforcement(self, response: Dict, analysis: Dict) -> Dict:
        """Apply enforcement based on violation analysis"""

        # Block progression if critical violations
        if analysis["blocked"]:
            response["blocked"] = True
            response["blockReason"] = "Critical thinking violations detected"
            response["mustComplete"] = analysis["must_complete"]

            # Force another thought to address issues
            response["nextThoughtNeeded"] = True
            response["thoughtGuidance"] = self._generate_guidance(analysis)

        # Add requirements even for non-blocking violations
        if analysis["must_complete"]:
            response["requirements"] = analysis["must_complete"]

        # Inject enforcement rules
        enforcement = analysis["enforcement"]
        if enforcement["level"] == "strict":
            response["strictMode"] = True
            response["blockedPhrases"] = enforcement["blocked_phrases"]
            response["requiredStructure"] = enforcement["required_structure"]

        # Add metacognitive prompt based on violations
        response["metacognitivePrompt"] = self._get_targeted_prompt(
            analysis["violations"]
        )

        return response

    def _generate_guidance(self, analysis: Dict) -> str:
        """Generate specific guidance based on violations"""

        violations = analysis["violations"]
        if not violations:
            return ""

        # Priority guidance based on most severe violation
        blockers = [v for v in violations if v.severity == "blocker"]
        if blockers:
            violation = blockers[0]

            if violation.type == ViolationType.REFLEXIVE_AGREEMENT:
                return """STOP: You're agreeing without analysis.
Required structure for next thought:
1. Three specific problems with this approach
2. Two alternative solutions
3. Evidence-based recommendation

You cannot use phrases like 'you're right' or 'great idea'."""

            elif violation.type == ViolationType.TECHNICAL_IMPOSSIBILITY:
                return """STOP: Technical impossibility detected.
Required for next thought:
1. Explain the technical constraint that makes this impossible
2. Propose an actually feasible alternative
3. Provide implementation details that work within constraints"""

            elif violation.type == ViolationType.REPEATING_FAILURE:
                return """STOP: This approach failed before.
Required for next thought:
1. Acknowledge the previous failure and why it happened
2. Explain what's different this time (if anything)
3. Use the successful pattern from KB instead"""

        # Less severe violations get lighter guidance
        errors = [v for v in violations if v.severity == "error"]
        if errors:
            return f"Address these issues: {', '.join(e.message for e in errors)}"

        warnings = [v for v in violations if v.severity == "warning"]
        if warnings:
            return f"Consider: {warnings[0].message}"

        return ""

    def _get_targeted_prompt(self, violations: list) -> str:
        """Generate metacognitive prompt based on specific violations"""

        if not violations:
            return None

        # Map violation types to targeted prompts
        prompt_map = {
            ViolationType.REFLEXIVE_AGREEMENT: "What specific problems might this approach cause?",
            ViolationType.TECHNICAL_IMPOSSIBILITY: "How would this actually work given the constraints?",
            ViolationType.UNVERIFIED_CLAIM: "What evidence supports this claim?",
            ViolationType.MISSING_ANALYSIS: "What are the tradeoffs and alternatives?",
            ViolationType.SHALLOW_THINKING: "What deeper analysis would an expert provide?",
            ViolationType.NO_EVIDENCE: "Where is the proof for this assertion?",
            ViolationType.REPEATING_FAILURE: "Why would this work when it failed before?",
        }

        # Return prompt for highest priority violation
        for violation in violations:
            if violation.type in prompt_map:
                return prompt_map[violation.type]

        return "Is this the level of analysis an expert would provide?"

    def _get_checkpoint_requirements(self) -> Dict[str, Any]:
        """Generate mandatory checkpoint requirements"""

        return {
            "required": True,
            "questions": [
                "What expertise have I added beyond basic execution?",
                "What future problems am I preventing?",
                "What patterns should I remember from this?",
            ],
            "must_answer_before_proceeding": True,
            "enforcement": "Cannot continue without addressing these questions",
        }

    def _init_kb_connection(self, connection_string: str):
        """Initialize connection to knowledge base"""
        # This would connect to the actual KB
        # For now, it's a placeholder
        pass

    def get_supervisor_stats(self) -> Dict[str, Any]:
        """Get statistics about supervisor interventions"""

        return {
            "thought_count": self.thought_count,
            "violation_history": self.supervisor.violation_count,
            "agreement_streak": self.supervisor.agreement_streak,
            "enforcement_active": self.enforcement_active,
        }

    def set_enforcement_level(self, level: str):
        """Adjust enforcement strictness"""

        levels = {
            "off": lambda: setattr(self, "enforcement_active", False),
            "normal": lambda: setattr(self, "enforcement_active", True),
            "strict": lambda: self._enable_strict_mode(),
            "maximum": lambda: self._enable_maximum_enforcement(),
        }

        if level in levels:
            levels[level]()

    def _enable_strict_mode(self):
        """Enable strict enforcement mode"""
        self.enforcement_active = True
        self.supervisor.agreement_streak = 2  # Lower threshold

    def _enable_maximum_enforcement(self):
        """Maximum enforcement for critical thinking"""
        self.enforcement_active = True
        self.supervisor.agreement_streak = 1  # Hair trigger
        # Would add more strict settings here


# Example of how this would be used in the MCP server
def handle_thinking_tool_request(request: Dict) -> Dict:
    """
    This would replace the current thinking tool handler
    """
    # Initialize or get singleton instance
    server = EnhancedThinkingServer(kb_connection_string="neo4j://localhost:7687")

    # Process with supervisor
    enhanced_response = server.process_thinking_request(request)

    # Return enhanced response
    return enhanced_response
