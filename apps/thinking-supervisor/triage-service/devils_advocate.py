"""
Devil's Advocate Agent - Questions assumptions and prevents tunnel vision
"""

import sys
from typing import Any, Dict, List, Optional

# Add paths for knowledge access
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

try:
    from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False


class DevilsAdvocate:
    """Agent that challenges thinking and questions assumptions"""
    
    def __init__(self):
        # Load operational instructions once
        self.operational_rules = self._load_operational_rules()
        
    def _load_operational_rules(self) -> List[str]:
        """Load key operational rules from knowledge base"""
        rules = [
            "NO ASSUMPTIONS - Verify everything, don't guess",
            "NO FALLBACKS - Fix root causes, not symptoms",
            "BE AN EXPERT ADVISOR - Question and evaluate, don't just execute",
            "CHECK SHARED RESOURCES - Don't modify what works for everything else",
            "UNDERSTAND BEFORE CHANGING - Know why code exists before modifying"
        ]
        
        if KNOWLEDGE_AVAILABLE:
            try:
                query_tool = get_enhanced_query()
                result = query_tool.query(
                    query_type="search",
                    query_text="GLOBAL OPERATIONAL INSTRUCTIONS",
                    limit=1
                )
                # Add any specific rules from KB
                for item in result.get("results", []):
                    content = item.get("content", "")
                    if "NO ASSUMPTIONS" in content:
                        # Extract key rules
                        rules.append("From KB: Question every assumption before acting")
            except:
                pass  # Use defaults if KB unavailable
                
        return rules
    
    def analyze(self, thought: str, intended_action: Optional[str], thought_data: Any) -> Dict:
        """
        Analyze the current thought and intended action for potential issues
        Returns critical questions and alternative approaches
        """
        
        questions = []
        alternatives = []
        warnings = []
        critical_violations = []  # STOP-level issues
        
        # Get step awareness
        thought_number = getattr(thought_data, "thoughtNumber", 1) if thought_data else 1
        total_thoughts = getattr(thought_data, "totalThoughts", 1) if thought_data else 1
        next_thought_needed = getattr(thought_data, "nextThoughtNeeded", False) if thought_data else False
        is_final_thought = not next_thought_needed or thought_number >= total_thoughts
        
        # CRITICAL: On final thought, be EXTRA skeptical
        if is_final_thought:
            questions.append("🎯 FINAL CHECK: Have you considered ALL angles of this problem?")
            questions.append("🎯 What haven't you thought about yet?")
            questions.append("🎯 Is there a simpler solution you're overlooking?")
            questions.append("🎯 What could go WRONG with this approach?")
            
            # Check if rushing to conclusion
            if thought_number <= 2:
                warnings.append("⚠️ Only {} thoughts before action - are you rushing?".format(thought_number))
                alternatives.append("Consider more exploration before committing to this solution")
            
            # Check confidence on final thought
            confidence = getattr(thought_data, "confidenceLevel", None) if thought_data else None
            if confidence and confidence < 70:
                critical_violations.append(f"🚨 FINAL THOUGHT with only {confidence}% confidence - TOO LOW to act!")
                alternatives.append("Do more thinking - your confidence should be 70%+ before acting")
        
        # Check for operational rule violations
        thought_lower = thought.lower()
        action_lower = intended_action.lower() if intended_action else ""
        
        # NO ASSUMPTIONS rule
        if any(word in thought_lower for word in ["probably", "should be", "i think", "assume", "must be"]):
            critical_violations.append("🚨 NO ASSUMPTIONS VIOLATION: You're guessing instead of verifying")
            questions.append("What EVIDENCE do you have for this assumption?")
            alternatives.append("STOP - Verify your assumption with actual testing first")
        
        # NO FALLBACKS rule  
        if "try/except" in thought_lower or "suppress" in thought_lower or "silence" in thought_lower:
            critical_violations.append("🚨 NO FALLBACKS VIOLATION: You're hiding errors instead of fixing them")
            questions.append("What's the ROOT CAUSE of this error?")
            alternatives.append("STOP - Understand why the error occurs before suppressing it")
        
        # Check for tunnel vision on errors
        if "error" in thought.lower() or "fix" in thought.lower():
            questions.append("Are you fixing the symptom or the root cause?")
            questions.append("Is there a simpler solution you're missing?")
            alternatives.append("Step back - what's the actual goal here?")
        
        # Check for modifying shared resources
        shared_indicators = ["interface", "shared", "common", "global", "base", "core"]
        if any(ind in thought.lower() for ind in shared_indicators):
            warnings.append("⚠️ You're about to modify a shared resource")
            questions.append("If this works for everything else, why would it be broken here?")
            questions.append("Should you really change shared code for your specific problem?")
            alternatives.append("Create a local override or wrapper instead")
        
        # Check for assumptions
        assumption_phrases = ["should", "probably", "i think", "assume", "must be", "obviously"]
        if any(phrase in thought.lower() for phrase in assumption_phrases):
            questions.append("What evidence do you have for that assumption?")
            questions.append("What if the opposite is true?")
            alternatives.append("Verify your assumption with a quick test first")
        
        # Check for complexity
        if len(thought) > 200 or "implement" in thought.lower() or "create" in thought.lower():
            questions.append("Is there an existing solution you could adapt?")
            questions.append("Could you solve 80% of this with 20% of the effort?")
            alternatives.append("Look for a library or existing code that does this")
        
        # Check confidence level
        confidence = getattr(thought_data, "confidenceLevel", None) if thought_data else None
        if confidence and confidence < 50:
            warnings.append(f"⚠️ Your confidence is only {confidence}%")
            questions.append("Should you research more before acting?")
            questions.append("Who or what could help increase your confidence?")
            alternatives.append("Run a small experiment to validate your approach")
        
        # Check attempt number
        attempts = getattr(thought_data, "attemptNumber", 1) if thought_data else 1
        if attempts > 2:
            warnings.append(f"⚠️ This is attempt #{attempts}")
            questions.append("Why didn't the previous approaches work?")
            questions.append("Are you repeating the same mistake?")
            alternatives.append("Try the OPPOSITE of what you've been doing")
            alternatives.append("Ask for help - fresh eyes might see what you're missing")
        
        # Check for action without understanding
        if intended_action and ("change" in intended_action.lower() or "modify" in intended_action.lower()):
            if "understand" not in thought.lower() and "know" not in thought.lower():
                warnings.append("⚠️ You're changing code you might not fully understand")
                questions.append("Do you understand WHY the current code is the way it is?")
                questions.append("What will break if you make this change?")
                alternatives.append("Read and understand the existing code first")
        
        # Proactive questioning about unconsidered aspects
        if not any(word in thought_lower for word in ["test", "verify", "check", "confirm"]):
            questions.append("How will you TEST that your solution works?")
        
        if not any(word in thought_lower for word in ["impact", "affect", "break", "depend"]):
            questions.append("What OTHER parts of the system might this affect?")
        
        if not any(word in thought_lower for word in ["user", "requirement", "goal", "purpose"]):
            questions.append("Does this actually solve the USER's problem?")
        
        if "error" in thought_lower and "why" not in thought_lower:
            questions.append("Do you understand WHY this error is occurring?")
        
        # Check for missing context
        user_request = getattr(thought_data, "userRequest", None) if thought_data else None
        if user_request and not any(word in thought_lower for word in user_request.lower().split()[:3]):
            warnings.append("⚠️ Your thought doesn't mention the user's actual request")
            questions.append(f"How does this relate to: {user_request[:50]}?")
        
        # Generate skeptical summary
        if critical_violations:
            skepticism_level = "critical"
            should_pause = True  # MUST stop
        elif warnings:
            skepticism_level = "high" if len(warnings) > 1 else "medium"
            should_pause = True  # Should stop
        elif questions:
            skepticism_level = "medium"
            should_pause = False  # Can continue but consider questions
        else:
            skepticism_level = "low"
            should_pause = False
        
        return {
            "critical_violations": critical_violations,  # NEW: Rule violations requiring stop
            "warnings": warnings,
            "questions": questions[:5],  # Top 5 most relevant
            "alternatives": alternatives[:3],  # Top 3 alternatives
            "skepticism_level": skepticism_level,
            "should_pause": should_pause,
            "summary": self._generate_summary(critical_violations, warnings, questions, alternatives)
        }
    
    def _generate_summary(self, critical_violations: List[str], warnings: List[str], questions: List[str], alternatives: List[str]) -> str:
        """Generate a concise summary of concerns"""
        if critical_violations:
            return f"CRITICAL: {critical_violations[0]} - YOU MUST STOP AND RECONSIDER"
        elif warnings:
            return f"STOP AND THINK: {warnings[0]}. {questions[0] if questions else ''}"
        elif questions:
            return f"Before you continue: {questions[0]}"
        elif alternatives:
            return f"Consider: {alternatives[0]}"
        else:
            return "Proceed with caution and verify assumptions"