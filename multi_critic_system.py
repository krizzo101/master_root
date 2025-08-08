#!/usr/bin/env python3
"""
Multi-Critic System Implementation

Implements a disciplined multi-critic pattern with:
- Parallel, independent critics with narrow charters
- Strict JSON output with standardized schema
- Consolidator that merges results into single verdict
- Anti-loop mechanisms and budget controls
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from openai import OpenAI
import os


class CriticType(Enum):
    CONTRACTS = "contracts"
    TESTS = "tests"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCS = "docs"


class FailureCategory(Enum):
    SYNTAX = "syntax"
    TEST = "test"
    CONTRACT = "contract"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCS = "docs"


@dataclass
class CriticConfig:
    """Configuration for individual critics."""

    critic_type: CriticType
    model: str = "o3"
    temperature: float = 0.0
    reasoning_effort: str = "low"  # low, medium
    max_output_tokens: int = 1000
    store_responses: bool = True
    include_reasoning: bool = True


@dataclass
class CriticResult:
    """Standardized result from any critic."""

    critic_type: CriticType
    verdict: str  # "accept" | "revise"
    scores: Dict[str, float]  # correctness, consistency, safety, efficiency, clarity
    failures: List[Dict[str, str]]  # category, evidence, location, minimal_fix_hint
    next_actions: List[str]
    confidence: float = 1.0
    reasoning_items_count: int = 0


@dataclass
class ConsolidatedResult:
    """Merged result from all critics."""

    verdict: str  # "accept" | "revise"
    scores: Dict[str, float]
    failures: List[Dict[str, str]]
    next_actions: List[str]
    blocking_failures: List[Dict[str, str]]
    summary_scores: Dict[str, float]
    iteration_count: int = 0
    total_critics: int = 0


class MultiCriticSystem:
    """
    Disciplined multi-critic system with parallel execution and consolidation.
    """

    def __init__(self, configs: Optional[List[CriticConfig]] = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.critic_configs = configs or self._get_default_configs()
        self.sessions = {}  # Track critic sessions for threading
        self.iteration_budget = 3  # Max iterations before giving up
        self.consolidator = CriticConsolidator()

        # Standardized schema for all critics
        self.critique_schema = self._get_critique_schema()

    def _get_default_configs(self) -> List[CriticConfig]:
        """Get default critic configurations."""
        return [
            CriticConfig(CriticType.CONTRACTS, max_output_tokens=800),
            CriticConfig(CriticType.TESTS, max_output_tokens=1000),
            CriticConfig(CriticType.SECURITY, max_output_tokens=800),
            CriticConfig(CriticType.PERFORMANCE, max_output_tokens=600),
            CriticConfig(CriticType.STYLE, max_output_tokens=600),
            CriticConfig(CriticType.DOCS, max_output_tokens=500),
        ]

    def _get_critique_schema(self) -> Dict[str, Any]:
        """Get standardized schema for all critics."""
        return {
            "name": "critic_result",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["verdict", "scores", "failures", "next_actions"],
                "properties": {
                    "verdict": {"type": "string", "enum": ["accept", "revise"]},
                    "scores": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "correctness",
                            "consistency",
                            "safety",
                            "efficiency",
                            "clarity",
                        ],
                        "properties": {
                            "correctness": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "consistency": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "safety": {"type": "number", "minimum": 0, "maximum": 1},
                            "efficiency": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "clarity": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                    "failures": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "category",
                                "evidence",
                                "location",
                                "minimal_fix_hint",
                            ],
                            "properties": {
                                "category": {"type": "string"},
                                "evidence": {
                                    "type": "string"
                                },  # concrete line/assert/log; no CoT
                                "location": {"type": "string"},
                                "minimal_fix_hint": {"type": "string"},
                            },
                        },
                    },
                    "next_actions": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            },
            "strict": True,
        }

    def start_session(self, session_id: str) -> str:
        """Start a new multi-critic session."""
        self.sessions[session_id] = {
            "iteration_count": 0,
            "critic_sessions": {},
            "previous_results": [],
            "frozen_contracts": set(),  # Anti-loop: freeze contracts
        }
        return session_id

    async def analyze_code(
        self, code: str, spec: str, session_id: str, iteration: int = 1
    ) -> ConsolidatedResult:
        """
        Analyze code with parallel critics and consolidate results.

        Args:
            code: The code to analyze
            spec: Original specification/requirements
            session_id: Session ID for threading
            iteration: Current iteration number

        Returns:
            Consolidated result with single verdict and ordered actions
        """

        if session_id not in self.sessions:
            self.start_session(session_id)

        session = self.sessions[session_id]
        session["iteration_count"] = iteration

        # Run critics in parallel
        critic_tasks = []
        for config in self.critic_configs:
            task = self._run_critic(config, code, spec, session_id, iteration)
            critic_tasks.append(task)

        # Wait for all critics to complete
        critic_results = await asyncio.gather(*critic_tasks, return_exceptions=True)

        # Filter out exceptions and convert to CriticResult objects
        valid_results = []
        for i, result in enumerate(critic_results):
            if isinstance(result, Exception):
                print(
                    f"Critic {self.critic_configs[i].critic_type.value} failed: {result}"
                )
                continue
            if result and result.get("status") == "success":
                valid_results.append(
                    self._parse_critic_result(
                        result, self.critic_configs[i].critic_type
                    )
                )

        # Consolidate results
        consolidated = self.consolidator.consolidate(valid_results)
        consolidated.iteration_count = iteration
        consolidated.total_critics = len(valid_results)

        # Store for anti-loop mechanisms
        session["previous_results"].append(consolidated)

        return consolidated

    async def _run_critic(
        self,
        config: CriticConfig,
        code: str,
        spec: str,
        session_id: str,
        iteration: int,
    ) -> Dict[str, Any]:
        """Run a single critic with threading support."""

        session = self.sessions[session_id]
        critic_session_key = f"{session_id}_{config.critic_type.value}"

        # Build critic-specific prompt
        prompt = self._build_critic_prompt(config.critic_type, code, spec, iteration)

        # Prepare API call parameters
        api_params = {
            "model": config.model,
            "input": [{"role": "developer", "content": prompt}],
            "response": {
                "modalities": ["text"],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "json_schema": self.critique_schema,
                    }
                },
            },
            "reasoning": {"effort": config.reasoning_effort},
            "max_output_tokens": config.max_output_tokens,
            "temperature": config.temperature,
            "store": config.store_responses,
        }

        # Add threading support
        if config.store_responses and critic_session_key in session["critic_sessions"]:
            api_params["previous_response_id"] = session["critic_sessions"][
                critic_session_key
            ]
        elif not config.store_responses and session.get("reasoning_items"):
            # Stateless threading with reasoning items
            previous_items = session["reasoning_items"][-2:]  # Last 2 reasoning items
            api_params["input"] = previous_items + [
                {"role": "developer", "content": prompt}
            ]
            api_params["include"] = ["reasoning.encrypted_content"]

        try:
            # Call o3 with structured output
            response = self.client.responses.create(**api_params)

            # Store response ID for threading
            if config.store_responses:
                session["critic_sessions"][critic_session_key] = response.id

            # Extract reasoning items
            reasoning_items = []
            for item in response.output:
                if hasattr(item, "type") and item.type == "reasoning":
                    reasoning_items.append(item)

            if "reasoning_items" not in session:
                session["reasoning_items"] = []
            session["reasoning_items"].extend(reasoning_items)

            # Parse structured output
            try:
                data = response.output_parsed
                return {
                    "status": "success",
                    "data": data,
                    "reasoning_items_count": len(reasoning_items),
                    "response_id": response.id,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to parse structured output: {e}",
                    "raw_output": str(response.output),
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _build_critic_prompt(
        self, critic_type: CriticType, code: str, spec: str, iteration: int
    ) -> str:
        """Build critic-specific prompt with tight charter."""

        base_prompt = f"""You are the {critic_type.value.upper()} CRITIC. Analyze the following code against the specification.

CODE TO ANALYZE:
{code}

ORIGINAL SPECIFICATION:
{spec}

ITERATION: {iteration}/3

"""

        # Add critic-specific guidance
        if critic_type == CriticType.CONTRACTS:
            base_prompt += """CONTRACTS CRITIC CHARTER:
- Verify function/class names & argument lists match specification exactly
- Check for signature mismatches, missing parameters, wrong return types
- Produce exact diffs: "got: func(x, y) vs expected: func(x, y, z)"
- Block on any contract violation
- Evidence: exact function signatures, parameter lists, return types

"""
        elif critic_type == CriticType.TESTS:
            base_prompt += """TESTS CRITIC CHARTER:
- Identify failing tests and missing test coverage
- Output failing test names + assertion lines
- Check if code handles edge cases and error conditions
- Propose ONE minimal test if coverage gap exists
- Evidence: test file names, assertion lines, error messages

"""
        elif critic_type == CriticType.SECURITY:
            base_prompt += """SECURITY CRITIC CHARTER:
- Check for secrets, unsafe subprocess calls, deserialization issues
- Look for injection vulnerabilities, unsafe file operations
- Verify proper input validation and sanitization
- Evidence: exact code lines with security issues

"""
        elif critic_type == CriticType.PERFORMANCE:
            base_prompt += """PERFORMANCE CRITIC CHARTER:
- Identify big-O hotspots, needless copies, inefficient algorithms
- Check for memory leaks, excessive allocations
- Only suggest safe micro-fixes
- Evidence: specific performance bottlenecks

"""
        elif critic_type == CriticType.STYLE:
            base_prompt += """STYLE CRITIC CHARTER:
- Check ruff/mypy alignment, code formatting
- Verify naming conventions, documentation standards
- Block only if parse/type errors exist
- Evidence: specific style violations

"""
        elif critic_type == CriticType.DOCS:
            base_prompt += """DOCS CRITIC CHARTER:
- Check for missing docstrings, unclear comments
- Verify README updates, API documentation
- Ensure examples are current and working
- Evidence: missing documentation sections

"""

        # Add iteration-specific severity
        if iteration == 1:
            base_prompt += (
                """FIRST ITERATION: Be thorough and systematic. Find ALL issues."""
            )
        elif iteration == 2:
            base_prompt += """SECOND ITERATION: Focus on remaining critical issues from iteration 1."""
        else:
            base_prompt += """FINAL ITERATION: Only address blocking issues that prevent code from working."""

        base_prompt += """

IMPORTANT:
- Provide concrete evidence, not vague suggestions
- Use exact line numbers, function names, error messages
- No chain-of-thought - just facts and evidence
- Be specific and actionable in next_actions
- Focus on your charter area only

OUTPUT: Return structured JSON with verdict, scores, failures, and next_actions."""

        return base_prompt

    def _parse_critic_result(
        self, result: Dict[str, Any], critic_type: CriticType
    ) -> CriticResult:
        """Parse API result into CriticResult object."""
        data = result["data"]

        return CriticResult(
            critic_type=critic_type,
            verdict=data["verdict"],
            scores=data["scores"],
            failures=data["failures"],
            next_actions=data["next_actions"],
            reasoning_items_count=result.get("reasoning_items_count", 0),
        )


class CriticConsolidator:
    """Consolidates results from multiple critics into single verdict."""

    def __init__(self):
        self.blocking_categories = {"syntax", "test", "contract", "security"}
        self.critic_priority = {
            CriticType.CONTRACTS: 0,
            CriticType.TESTS: 1,
            CriticType.SECURITY: 2,
            CriticType.PERFORMANCE: 3,
            CriticType.STYLE: 4,
            CriticType.DOCS: 5,
        }

    def consolidate(self, critic_results: List[CriticResult]) -> ConsolidatedResult:
        """Consolidate multiple critic results into single verdict."""

        if not critic_results:
            return ConsolidatedResult(
                verdict="accept",
                scores={
                    "correctness": 1.0,
                    "consistency": 1.0,
                    "safety": 1.0,
                    "efficiency": 1.0,
                    "clarity": 1.0,
                },
                failures=[],
                next_actions=[],
                blocking_failures=[],
                summary_scores={},
            )

        # Determine overall verdict
        verdict = "accept"
        all_failures = []
        all_actions = []

        for result in critic_results:
            all_failures.extend(result.failures)
            all_actions.extend(result.next_actions)

            # Check for blocking failures
            if result.verdict == "revise":
                for failure in result.failures:
                    if failure["category"] in self.blocking_categories:
                        verdict = "revise"
                        break

        # Consolidate scores (average, but min blocking dimensions)
        scores = defaultdict(list)
        for result in critic_results:
            for dimension, score in result.scores.items():
                scores[dimension].append(score)

        avg_scores = {
            dim: sum(scores_list) / len(scores_list)
            for dim, scores_list in scores.items()
        }

        # Make blocking dimensions pessimistic (min)
        blocking_dimensions = {"correctness", "consistency", "safety"}
        for dim in blocking_dimensions:
            if scores.get(dim):
                avg_scores[dim] = min(scores[dim])

        # De-duplicate actions
        seen_actions = set()
        dedup_actions = []
        for action in all_actions:
            key = action.strip().lower()
            if key not in seen_actions:
                seen_actions.add(key)
                dedup_actions.append(action)

        # Sort actions by priority
        def action_priority(action: str) -> int:
            action_lower = action.lower()
            if any(
                term in action_lower
                for term in ["fix failing test", "update signature", "syntax"]
            ):
                return 0
            if "security" in action_lower or "secrets" in action_lower:
                return 1
            if "perf" in action_lower or "optimize" in action_lower:
                return 3
            if "style" in action_lower or "lint" in action_lower:
                return 4
            return 2

        dedup_actions.sort(key=action_priority)

        # Identify blocking failures
        blocking_failures = [
            failure
            for failure in all_failures
            if failure["category"] in self.blocking_categories
        ]

        return ConsolidatedResult(
            verdict=verdict,
            scores=avg_scores,
            failures=all_failures,
            next_actions=dedup_actions,
            blocking_failures=blocking_failures,
            summary_scores=avg_scores,
            total_critics=len(critic_results),
        )


# Example usage
async def main():
    """Example usage of the multi-critic system."""

    # Initialize system
    multi_critic = MultiCriticSystem()

    # Test code with issues
    test_code = """
    def calculate_total(items, tax_rate):
        total = sum(items)
        return total * (1 + tax_rate)

    # Missing test coverage
    def process_user_data(user_input):
        return user_input.strip()  # No validation
    """

    spec = """
    Requirements:
    - calculate_total: should handle empty items list
    - process_user_data: should validate input and handle None
    - All functions should have docstrings
    - Should include unit tests
    """

    # Start session and analyze
    session_id = multi_critic.start_session("test_session_001")

    result = await multi_critic.analyze_code(
        code=test_code, spec=spec, session_id=session_id, iteration=1
    )

    print("=== MULTI-CRITIC ANALYSIS RESULT ===")
    print(f"Verdict: {result.verdict}")
    print(f"Total Critics: {result.total_critics}")
    print(f"Scores: {result.summary_scores}")
    print(f"Blocking Failures: {len(result.blocking_failures)}")
    print(f"Next Actions: {len(result.next_actions)}")

    if result.next_actions:
        print("\nOrdered Actions:")
        for i, action in enumerate(result.next_actions[:5], 1):
            print(f"{i}. {action}")


if __name__ == "__main__":
    asyncio.run(main())
