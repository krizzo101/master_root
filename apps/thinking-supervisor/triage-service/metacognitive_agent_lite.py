"""Ultra-lightweight metacognitive agent - optimized for speed"""

import json
import time
from typing import Any, Dict, List


class MetacognitiveAgentLite:
    """Simplified, fast metacognitive analysis"""

    def __init__(self):
        self.interface = None

    def analyze(
        self,
        thought_number: int,
        total_thoughts: int,
        thought: str,
        recent_thoughts: List,
        instructions: str = "",
        thought_data: Any = None,
        session_id: str = "default",
    ) -> Dict:
        """Single ultra-fast analysis replacing 4 agents"""

        start_time = time.time()

        # Get phase from thought_data
        phase = (
            getattr(thought_data, "workPhase", "unknown") if thought_data else "unknown"
        )

        # Quick rule checks (no LLM needed)
        violations = []
        if "probably" in thought.lower() or "likely" in thought.lower():
            violations.append(
                {
                    "rule": "NO_ASSUMPTIONS",
                    "severity": "medium" if phase == "research" else "high",
                }
            )

        if "gpt-4o" in thought:
            violations.append({"rule": "MODELS_2025", "severity": "critical"})

        # Quick pattern detection
        patterns = []
        if recent_thoughts and len(recent_thoughts) > 2:
            # Check for repetition
            recent_text = " ".join(str(t) for t in recent_thoughts[-3:])
            if thought[:50] in recent_text:
                patterns.append({"type": "REPETITION", "severity": "medium"})

        # Quick progress check
        progress_ratio = thought_number / max(total_thoughts, 1)
        if progress_ratio > 1.2:
            progress = {"status": "behind", "ratio": progress_ratio}
        elif progress_ratio > 0.8:
            progress = {"status": "on_track", "ratio": progress_ratio}
        else:
            progress = {"status": "ahead", "ratio": progress_ratio}

        # Risk scoring (simple calculation)
        risk_score = 0
        risk_score += len(violations) * 20
        risk_score += len(patterns) * 10
        if progress["status"] == "behind":
            risk_score += 20

        # Generate coaching only for high risk
        coaching = ""
        if risk_score >= 40:
            if violations:
                coaching = f"Note: {violations[0]['rule']} detected. "
            if progress["status"] == "behind":
                coaching += (
                    f"You're at thought {thought_number}/{total_thoughts}. "
                    "Focus on essentials."
                )

        elapsed = time.time() - start_time

        return {
            "thought_number": thought_number,
            "analysis_time": round(elapsed, 2),
            "violations": violations,
            "patterns": patterns,
            "progress": progress,
            "risk_score": risk_score,
            "coaching": coaching,
            "session_id": session_id,
        }


class MetacognitiveAgentSmart:
    """Smart version with single LLM call instead of 4"""

    def __init__(self, interface=None):
        self.interface = interface

    def analyze(
        self,
        thought_number: int,
        total_thoughts: int,
        thought: str,
        recent_thoughts: List,
        instructions: str = "",
        thought_data: Any = None,
        session_id: str = "default",
    ) -> Dict:
        """Single consolidated LLM call for all analysis"""

        start_time = time.time()

        # Get phase and context
        phase = (
            getattr(thought_data, "workPhase", "unknown") if thought_data else "unknown"
        )
        action = getattr(thought_data, "intendedAction", "") if thought_data else ""

        # Build minimal prompt
        prompt = f"""Analyze this AI thought for risks and improvements.

Phase: {phase}
Thought {thought_number}/{total_thoughts}: {thought[:200]}
Action: {action}

Check for:
1. Assumptions (words like probably/likely)
2. Wrong models (gpt-4o forbidden)
3. Repetition or stuck patterns
4. Progress issues

Return JSON:
{{"risk": 0-100, "issues": ["brief issue"], "suggestion": "brief advice"}}"""

        try:
            if self.interface:
                # Single fast API call
                response = self.interface.responses_create(
                    model="gpt-5-nano",
                    input=prompt,
                    instructions="Brief risk assessment. Be concise.",
                    reasoning_effort="low",
                )

                # Parse response
                content = (
                    response.output[0].content[0].text if response.output else "{}"
                )
                result = json.loads(content)
            else:
                # Fallback without LLM
                result = {"risk": 0, "issues": [], "suggestion": ""}

        except Exception as e:
            print(f"Analysis error: {e}")
            result = {"risk": 0, "issues": [], "suggestion": ""}

        elapsed = time.time() - start_time

        return {
            "thought_number": thought_number,
            "analysis_time": round(elapsed, 2),
            "risk_score": result.get("risk", 0),
            "issues": result.get("issues", []),
            "coaching": result.get("suggestion", ""),
            "session_id": session_id,
        }
