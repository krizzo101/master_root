#!/usr/bin/env python3
"""
Multi-Critic Integration with Main Agent

Shows how to integrate the multi-critic system with the optimized main agent
in a complete development workflow with anti-loop mechanisms.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from multi_critic_system import MultiCriticSystem, ConsolidatedResult
from optimized_main_agent import OptimizedMainAgent, AgentConfig


@dataclass
class DevelopmentSession:
    """Tracks a complete development session with main agent and critics."""

    session_id: str
    task: str
    spec: str
    iteration_count: int = 0
    max_iterations: int = 3
    current_code: str = ""
    consolidated_results: List[ConsolidatedResult] = None

    def __post_init__(self):
        if self.consolidated_results is None:
            self.consolidated_results = []


class MultiCriticWorkflow:
    """
    Complete workflow integrating main agent with multi-critic system.

    Pattern:
    1. Main agent generates code
    2. Multi-critic analyzes in parallel
    3. Consolidator provides single verdict + ordered actions
    4. Main agent applies fixes
    5. Repeat until accept or budget exhausted
    """

    def __init__(self):
        self.main_agent = OptimizedMainAgent()
        self.multi_critic = MultiCriticSystem()
        self.sessions = {}

    def start_development_session(
        self, session_id: str, task: str, spec: str
    ) -> DevelopmentSession:
        """Start a new development session."""
        session = DevelopmentSession(session_id=session_id, task=task, spec=spec)
        self.sessions[session_id] = session

        # Start threading sessions
        self.main_agent.start_conversation(session_id)
        self.multi_critic.start_session(session_id)

        return session

    async def develop_with_critics(
        self, session_id: str, task: str, spec: str
    ) -> Dict[str, Any]:
        """
        Complete development workflow with multi-critic feedback loop.

        Args:
            session_id: Unique session identifier
            task: Development task description
            spec: Original specification/requirements

        Returns:
            Final result with code, metrics, and development history
        """

        # Start session
        session = self.start_development_session(session_id, task, spec)

        # Development loop
        while session.iteration_count < session.max_iterations:
            session.iteration_count += 1

            print(
                f"\n=== ITERATION {session.iteration_count}/{session.max_iterations} ==="
            )

            # Step 1: Generate/update code with main agent
            if session.iteration_count == 1:
                # Initial code generation
                result = self.main_agent.generate_code(
                    task=task,
                    context=spec,
                    task_type="code_generation",
                    complexity="medium",
                    session_id=session_id,
                )
                session.current_code = result["code"]
            else:
                # Apply fixes from previous critic feedback
                last_result = session.consolidated_results[-1]
                if last_result.verdict == "accept":
                    print("✅ Code accepted by all critics!")
                    break

                # Apply ordered actions
                session.current_code = await self._apply_critic_fixes(
                    session.current_code, last_result.next_actions
                )

            # Step 2: Run multi-critic analysis
            print("🔍 Running multi-critic analysis...")
            critic_result = await self.multi_critic.analyze_code(
                code=session.current_code,
                spec=spec,
                session_id=session_id,
                iteration=session.iteration_count,
            )

            session.consolidated_results.append(critic_result)

            # Step 3: Check for acceptance or budget exhaustion
            if critic_result.verdict == "accept":
                print("✅ All critics accept the code!")
                break

            if session.iteration_count >= session.max_iterations:
                print("⚠️ Development budget exhausted")
                break

            # Step 4: Show next actions for next iteration
            print(f"📋 Next actions ({len(critic_result.next_actions)}):")
            for i, action in enumerate(critic_result.next_actions[:3], 1):
                print(f"  {i}. {action}")
            if len(critic_result.next_actions) > 3:
                print(f"  ... and {len(critic_result.next_actions) - 3} more")

        # Return final result
        return self._build_final_result(session)

    async def _apply_critic_fixes(self, current_code: str, actions: List[str]) -> str:
        """
        Apply critic-suggested fixes to the code.

        This is a simplified implementation. In practice, you'd want:
        - AST-based code modification
        - Proper diff application
        - Validation of changes
        """

        # For demonstration, we'll use the main agent to apply fixes
        fix_prompt = f"""Apply the following fixes to the code:

CURRENT CODE:
{current_code}

FIXES TO APPLY:
{chr(10).join(f"- {action}" for action in actions[:5])}  # Limit to first 5 fixes

Apply these fixes systematically and return the updated code."""

        result = self.main_agent.generate_code(
            task=fix_prompt, task_type="bug_fix", complexity="low"
        )

        return result["code"]

    def _build_final_result(self, session: DevelopmentSession) -> Dict[str, Any]:
        """Build final result from development session."""

        final_critic_result = (
            session.consolidated_results[-1] if session.consolidated_results else None
        )

        return {
            "session_id": session.session_id,
            "task": session.task,
            "final_code": session.current_code,
            "iteration_count": session.iteration_count,
            "max_iterations": session.max_iterations,
            "final_verdict": final_critic_result.verdict
            if final_critic_result
            else "unknown",
            "final_scores": final_critic_result.summary_scores
            if final_critic_result
            else {},
            "total_critics_used": final_critic_result.total_critics
            if final_critic_result
            else 0,
            "development_history": [
                {
                    "iteration": i + 1,
                    "verdict": result.verdict,
                    "scores": result.summary_scores,
                    "blocking_failures": len(result.blocking_failures),
                    "next_actions": len(result.next_actions),
                }
                for i, result in enumerate(session.consolidated_results)
            ],
            "success": final_critic_result.verdict == "accept"
            if final_critic_result
            else False,
        }


class AntiLoopMechanisms:
    """Anti-loop mechanisms to prevent infinite development cycles."""

    @staticmethod
    def check_for_oscillation(history: List[Dict[str, Any]]) -> bool:
        """Check if the development is oscillating between states."""
        if len(history) < 3:
            return False

        # Check if we're alternating between accept/revise
        recent_verdicts = [h["verdict"] for h in history[-3:]]
        if recent_verdicts == ["revise", "accept", "revise"]:
            return True

        # Check if scores are not improving
        recent_scores = [h["scores"].get("correctness", 0) for h in history[-3:]]
        if len(recent_scores) >= 3 and recent_scores[-1] <= recent_scores[-3]:
            return True

        return False

    @staticmethod
    def freeze_contracts(session: DevelopmentSession) -> bool:
        """Freeze contracts to prevent API signature changes."""
        # Implementation would track API signatures and prevent changes
        # unless explicitly approved by contracts critic
        return True

    @staticmethod
    def check_budget_exhaustion(session: DevelopmentSession) -> bool:
        """Check if development budget is exhausted."""
        return session.iteration_count >= session.max_iterations


# Example usage
async def main():
    """Example of complete multi-critic development workflow."""

    workflow = MultiCriticWorkflow()

    # Example development task
    task = """Create a simple email validation function with the following requirements:
    - Function name: validate_email
    - Input: email string
    - Output: boolean indicating if email is valid
    - Should handle common email formats
    - Should reject obviously invalid emails
    - Include proper error handling
    - Add comprehensive unit tests
    - Include docstring documentation"""

    spec = """Email Validation Function Specification:

    Function: validate_email(email: str) -> bool

    Requirements:
    1. Accept valid email formats (user@domain.com, user.name@domain.co.uk)
    2. Reject invalid formats (no @, no domain, invalid characters)
    3. Handle edge cases (empty string, None, whitespace)
    4. Include comprehensive unit tests
    5. Add proper docstring with examples
    6. Follow Python naming conventions
    7. Include type hints

    Test cases to cover:
    - Valid emails: test@example.com, user.name@domain.co.uk
    - Invalid emails: invalid, @domain.com, user@, user@domain
    - Edge cases: "", None, "   test@example.com   "
    """

    # Run development workflow
    print("🚀 Starting multi-critic development workflow...")
    result = await workflow.develop_with_critics(
        session_id="email_validation_001", task=task, spec=spec
    )

    # Display results
    print("\n" + "=" * 60)
    print("🎯 DEVELOPMENT WORKFLOW COMPLETE")
    print("=" * 60)
    print(f"Session ID: {result['session_id']}")
    print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print(f"Iterations: {result['iteration_count']}/{result['max_iterations']}")
    print(f"Final Verdict: {result['final_verdict']}")
    print(f"Total Critics Used: {result['total_critics_used']}")

    if result["final_scores"]:
        print(f"\nFinal Scores:")
        for dimension, score in result["final_scores"].items():
            print(f"  {dimension}: {score:.2f}")

    print(f"\nDevelopment History:")
    for entry in result["development_history"]:
        status = "✅" if entry["verdict"] == "accept" else "🔄"
        print(
            f"  Iteration {entry['iteration']}: {status} {entry['verdict']} "
            f"(scores: {entry['scores'].get('correctness', 0):.2f}, "
            f"actions: {entry['next_actions']})"
        )

    print(f"\nFinal Code Length: {len(result['final_code'])} characters")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
