#!/usr/bin/env python3
"""
Optimized Critic Agent Implementation

Enhanced critic using o3 model with structured JSON output and reasoning threading.
Incorporates GPT-5 best practices for systematic issue resolution.
"""

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass
class CriticConfig:
    """Configuration for the optimized critic agent."""

    model: str = "o3"  # o3 for reasoning, o4-mini for speed
    max_output_tokens: int = 2000
    temperature: float = 0.0
    store_responses: bool = True  # Enable stateful conversations with reasoning
    include_reasoning: bool = True  # Include reasoning items for o-series


class OptimizedCriticAgent:
    """
    Optimized critic agent using o3 model with structured JSON output.

    Key improvements:
    - Structured JSON output for machine-readable feedback
    - Severity-based iteration approach
    - Concrete evidence collection
    - Reasoning threading for o3 model
    - Accountability tracking
    """

    def __init__(self, config: CriticConfig = None):
        self.config = config or CriticConfig()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.critic_sessions = {}  # Track critic sessions with reasoning

    def start_critic_session(self, session_id: str) -> str:
        """Start a new critic session with reasoning threading."""
        self.critic_sessions[session_id] = {
            "current_response_id": None,
            "reasoning_items": [],
            "iteration_count": 0,
            "issues_found": [],
            "fixes_provided": [],
        }
        return session_id

    def analyze_code_with_structured_feedback(
        self,
        code: str,
        session_id: str,
        iteration: int = 1,
        previous_feedback: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze code with structured JSON feedback using o3 model.

        Args:
            code: The code to analyze
            session_id: Session ID for threading
            iteration: Current iteration number (1-3)
            previous_feedback: Previous feedback to build upon

        Returns:
            Structured JSON feedback with concrete fixes
        """

        if session_id not in self.critic_sessions:
            self.start_critic_session(session_id)

        session = self.critic_sessions[session_id]
        session["iteration_count"] = iteration

        # Build iteration-specific prompt
        prompt = self._build_iteration_prompt(code, iteration, previous_feedback)

        # Prepare API call parameters
        api_params = {
            "model": self.config.model,
            "input": [{"role": "developer", "content": prompt}],
            "text": {"format": {"type": "json_object"}},  # Structured JSON output
            "max_output_tokens": self.config.max_output_tokens,
            "temperature": self.config.temperature,
            "store": self.config.store_responses,  # Enable stateful conversations
        }

        # Add reasoning threading for o3 model
        if self.config.include_reasoning and session["current_response_id"]:
            api_params["previous_response_id"] = session["current_response_id"]

        try:
            # Use o3 with structured output and reasoning threading
            response = self.client.responses.create(**api_params)

            # Store response ID and reasoning items for next iteration
            session["current_response_id"] = response.id

            # Extract reasoning items for o3 model
            reasoning_items = []
            for item in response.output:
                if hasattr(item, "type") and item.type == "reasoning":
                    reasoning_items.append(item)

            session["reasoning_items"].extend(reasoning_items)

            # Parse structured JSON feedback
            feedback_text = ""
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            feedback_text += content.text

            try:
                structured_feedback = json.loads(feedback_text)
            except json.JSONDecodeError:
                # Fallback to unstructured feedback
                structured_feedback = {
                    "status": "error",
                    "message": "Failed to parse structured feedback",
                    "raw_feedback": feedback_text,
                }

            # Update session tracking
            if "issues" in structured_feedback:
                session["issues_found"].extend(structured_feedback["issues"])
            if "fixes" in structured_feedback:
                session["fixes_provided"].extend(structured_feedback["fixes"])

            return {
                "session_id": session_id,
                "iteration": iteration,
                "structured_feedback": structured_feedback,
                "reasoning_items_count": len(reasoning_items),
                "total_reasoning_items": len(session["reasoning_items"]),
                "threaded": session["current_response_id"] is not None,
                "session_stats": {
                    "total_issues": len(session["issues_found"]),
                    "total_fixes": len(session["fixes_provided"]),
                    "iterations_completed": session["iteration_count"],
                },
            }

        except Exception as e:
            return {
                "session_id": session_id,
                "iteration": iteration,
                "error": str(e),
                "status": "error",
            }

    def _build_iteration_prompt(
        self, code: str, iteration: int, previous_feedback: str | None = None
    ) -> str:
        """Build iteration-specific prompt for systematic analysis."""

        base_prompt = f"""You are an expert code critic using the o3 model. Analyze the following code and provide structured JSON feedback.

CODE TO ANALYZE:
{code}

ITERATION: {iteration}/3

"""

        # Add iteration-specific guidance
        if iteration == 1:
            base_prompt += """FIRST ITERATION (RUTHLESS):
- Find ALL issues, no matter how small
- Be extremely thorough and systematic
- Focus on critical issues that prevent code from running
- Identify architectural problems and security vulnerabilities
- Don't hold back - find everything wrong

"""
        elif iteration == 2:
            base_prompt += """SECOND ITERATION (MODERATE):
- Focus on the most critical issues from iteration 1
- Provide concrete, actionable fixes
- Prioritize functional correctness over style
- Address security and performance issues
- Ensure fixes are specific and implementable

"""
        else:  # iteration == 3
            base_prompt += """THIRD ITERATION (LIGHT):
- Only address blocking issues that prevent code from working
- Focus on final validation and polish
- Ensure all critical fixes are complete
- Verify code is production-ready
- Minimal changes only

"""

        # Add previous feedback context if available
        if previous_feedback:
            base_prompt += f"""PREVIOUS FEEDBACK TO BUILD UPON:
{previous_feedback}

"""

        base_prompt += """REQUIRED OUTPUT FORMAT (JSON):
{
  "status": "success|error",
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "syntax|functional|security|performance|style",
      "description": "Clear description of the issue",
      "location": "File:line or specific location",
      "evidence": "Concrete evidence from the code",
      "impact": "What this issue affects"
    }
  ],
  "fixes": [
    {
      "issue_id": "Reference to issue above",
      "fix_type": "code_change|architecture|configuration|dependency",
      "current_code": "What's wrong",
      "fixed_code": "What it should be",
      "reasoning": "Why this fix is needed",
      "atomic_fix": "≤140 character fix description for nano model"
    }
  ],
  "priorities": [
    "List of atomic fixes in priority order for nano model"
  ],
  "next_actions": [
    "Specific next steps for the nano model"
  ],
  "confidence": "high|medium|low",
  "estimated_effort": "minutes to implement all fixes"
}

IMPORTANT:
- Provide concrete evidence, not vague suggestions
- Give specific code changes with exact locations
- Prioritize critical issues that prevent code from running
- Make atomic fixes ≤140 characters for nano model
- Use structured JSON format for machine readability
- Be systematic and thorough in analysis"""

        return base_prompt

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """Get summary of critic session performance."""
        if session_id not in self.critic_sessions:
            return {"error": "Session not found"}

        session = self.critic_sessions[session_id]

        # Calculate performance metrics
        critical_issues = len(
            [i for i in session["issues_found"] if i.get("severity") == "critical"]
        )
        high_issues = len(
            [i for i in session["issues_found"] if i.get("severity") == "high"]
        )

        return {
            "session_id": session_id,
            "iterations_completed": session["iteration_count"],
            "total_issues_found": len(session["issues_found"]),
            "critical_issues": critical_issues,
            "high_priority_issues": high_issues,
            "total_fixes_provided": len(session["fixes_provided"]),
            "reasoning_items_used": len(session["reasoning_items"]),
            "threaded_conversation": session["current_response_id"] is not None,
            "performance_rating": self._calculate_performance_rating(session),
        }

    def _calculate_performance_rating(self, session: dict) -> str:
        """Calculate critic performance rating."""
        total_issues = len(session["issues_found"])
        total_fixes = len(session["fixes_provided"])

        if total_issues == 0:
            return "NO_ISSUES_FOUND"
        elif total_fixes == 0:
            return "POOR - Found issues but no fixes"
        elif total_fixes < total_issues * 0.5:
            return "NEEDS_IMPROVEMENT - Less than 50% of issues have fixes"
        elif total_fixes < total_issues * 0.8:
            return "GOOD - Most issues have fixes"
        else:
            return "EXCELLENT - Comprehensive fix coverage"

    def validate_fixes(self, fixes: list[dict], original_code: str) -> dict[str, Any]:
        """Validate that provided fixes are implementable."""
        valid_fixes = []
        invalid_fixes = []

        for fix in fixes:
            # Basic validation
            if self._is_fix_valid(fix, original_code):
                valid_fixes.append(fix)
            else:
                invalid_fixes.append(fix)

        return {
            "valid_fixes": valid_fixes,
            "invalid_fixes": invalid_fixes,
            "validation_rate": len(valid_fixes) / max(1, len(fixes)),
            "total_fixes": len(fixes),
        }

    def _is_fix_valid(self, fix: dict, original_code: str) -> bool:
        """Check if a fix is valid and implementable."""
        # Basic validation checks
        required_fields = ["current_code", "fixed_code", "atomic_fix"]

        # Check required fields
        if not all(field in fix for field in required_fields):
            return False

        # Check if current_code exists in original code
        if fix["current_code"] not in original_code:
            return False

        # Check atomic fix length
        if len(fix["atomic_fix"]) > 140:
            return False

        return True


# Example usage
if __name__ == "__main__":
    # Test the optimized critic
    critic = OptimizedCriticAgent()

    # Test code with issues
    test_code = """
    from fastapi import FastAPI
    app = FastAPI()

    # Critical issue: Global JWT reference
    jwt_manager = app.state.jwt

    # High priority issue: Silent exception
    try:
        result = database.query()
    except Exception as e:
        pass
    """

    # Start critic session
    session_id = critic.start_critic_session("test_critic_001")

    # First iteration (ruthless)
    result1 = critic.analyze_code_with_structured_feedback(
        code=test_code, session_id=session_id, iteration=1
    )

    print("=== OPTIMIZED CRITIC TEST ===")
    print(f"First iteration - Status: {result1.get('status', 'success')}")
    print(f"Threaded: {result1.get('threaded', False)}")
    print(f"Reasoning items: {result1.get('reasoning_items_count', 0)}")

    # Get session summary
    summary = critic.get_session_summary(session_id)
    print(f"Session summary: {summary}")
