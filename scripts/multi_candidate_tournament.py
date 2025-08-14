#!/usr/bin/env python3
"""
Multi-Candidate Tournament System

Implements N-best with critic selection pattern:
1. Generate K candidates from main agent (GPT-5)
2. Pre-gate each candidate (AST, contracts, lint)
3. Parallel critics (o3) score each candidate independently
4. Consolidate + pick winner
5. Improve winner with synthesizer
"""

import ast
import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openai import OpenAI


class CandidateStatus(Enum):
    GENERATED = "generated"
    PRE_GATED = "pre_gated"
    CRITICIZED = "criticized"
    SELECTED = "selected"
    IMPROVED = "improved"


@dataclass
class Candidate:
    """Represents a single candidate solution."""

    candidate_id: str
    files: list[dict[str, str]]  # [{"path": "...", "content": "..."}]
    tests: list[dict[str, str]] = field(default_factory=list)
    notes: str = ""
    status: CandidateStatus = CandidateStatus.GENERATED
    scores: dict[str, float] = field(default_factory=dict)
    failures: list[dict[str, str]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    weighted_score: float = 0.0
    blocking_failures: list[dict[str, str]] = field(default_factory=list)


@dataclass
class TournamentConfig:
    """Configuration for the tournament system."""

    num_candidates: int = 3
    max_file_lines: int = 200
    temperature_range: tuple[float, float] = (0.1, 0.2)
    enable_pre_gating: bool = True
    enable_synthesis: bool = True
    max_iterations: int = 3


class MultiCandidateTournament:
    """
    Multi-candidate tournament system with critic selection.
    """

    def __init__(self, config: TournamentConfig = None):
        self.config = config or TournamentConfig()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sessions = {}

        # Standardized schemas
        self.candidate_schema = self._get_candidate_schema()
        self.critic_schema = self._get_critic_schema()
        self.synthesis_schema = self._get_synthesis_schema()

    def _get_candidate_schema(self) -> dict[str, Any]:
        """Schema for candidate generation output."""
        return {
            "name": "candidate_result",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["candidate_id", "files"],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["path", "content"],
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["path", "content"],
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "notes": {"type": "string"},
                },
            },
            "strict": True,
        }

    def _get_critic_schema(self) -> dict[str, Any]:
        """Schema for critic evaluation output."""
        return {
            "name": "critic_result",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "candidate_id",
                    "verdict",
                    "scores",
                    "failures",
                    "next_actions",
                ],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["accept", "revise"]},
                    "scores": {
                        "type": "object",
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
                            "required": [
                                "category",
                                "evidence",
                                "location",
                                "minimal_fix_hint",
                            ],
                            "properties": {
                                "category": {"type": "string"},
                                "evidence": {"type": "string"},
                                "location": {"type": "string"},
                                "minimal_fix_hint": {"type": "string"},
                            },
                        },
                    },
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                },
            },
            "strict": True,
        }

    def _get_synthesis_schema(self) -> dict[str, Any]:
        """Schema for synthesis output."""
        return {
            "name": "synthesis_result",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["files", "tests", "changes_made"],
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["path", "content"],
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["path", "content"],
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "changes_made": {"type": "string"},
                },
            },
            "strict": True,
        }

    def start_tournament(self, session_id: str) -> str:
        """Start a new tournament session."""
        self.sessions[session_id] = {
            "candidates": {},
            "critic_results": {},
            "iteration_count": 0,
            "frozen_contracts": set(),  # Anti-loop: freeze contracts
        }
        return session_id

    async def run_tournament(
        self, task: str, spec: str, session_id: str
    ) -> dict[str, Any]:
        """
        Run complete tournament workflow.

        Args:
            task: Development task
            spec: Original specification
            session_id: Session identifier

        Returns:
            Tournament result with winner, runner-up, and metrics
        """

        if session_id not in self.sessions:
            self.start_tournament(session_id)

        session = self.sessions[session_id]
        session["iteration_count"] += 1

        print(f"🏆 Starting Tournament (Iteration {session['iteration_count']})")

        # Step 1: Generate K candidates
        print("📝 Generating candidates...")
        candidates = await self._generate_candidates(task, spec, session_id)

        # Step 2: Pre-gate candidates (cheap, mechanical)
        if self.config.enable_pre_gating:
            print("🔍 Pre-gating candidates...")
            candidates = await self._pre_gate_candidates(candidates)

        # Step 3: Parallel critics score each candidate
        print("🎯 Running critics in parallel...")
        critic_results = await self._run_critics_parallel(candidates, spec, session_id)

        # Step 4: Consolidate and pick winner
        print("🏅 Consolidating results...")
        tournament_result = self._consolidate_and_select(candidates, critic_results)

        # Step 5: Improve winner (optional)
        if self.config.enable_synthesis and tournament_result["winner"]:
            print("🔧 Synthesizing improvements...")
            improved_winner = await self._synthesize_improvements(
                tournament_result["winner"],
                tournament_result["runner_up"],
                tournament_result["all_critic_actions"],
                session_id,
            )
            tournament_result["improved_winner"] = improved_winner

        return tournament_result

    async def _generate_candidates(
        self, task: str, spec: str, session_id: str
    ) -> list[Candidate]:
        """Generate K diverse candidates using GPT-5."""

        candidates = []
        design_levers = [
            "functional programming approach",
            "object-oriented design",
            "async/await patterns",
            "error handling with exceptions",
            "error handling with Result types",
            "minimal dependencies",
            "comprehensive logging",
            "type hints throughout",
            "defensive programming",
            "performance-optimized",
        ]

        for i in range(self.config.num_candidates):
            # Use different design levers and temperature for diversity
            design_lever = design_levers[i % len(design_levers)]
            temperature = self.config.temperature_range[0] + (i * 0.05) % (
                self.config.temperature_range[1] - self.config.temperature_range[0]
            )

            prompt = self._build_candidate_prompt(task, spec, design_lever, i + 1)

            try:
                response = self.client.responses.create(
                    model="gpt-5-nano",
                    input=[{"role": "developer", "content": prompt}],
                    response={
                        "modalities": ["text"],
                        "text": {
                            "format": {
                                "type": "json_schema",
                                "json_schema": self.candidate_schema,
                            }
                        },
                    },
                    temperature=temperature,
                    max_output_tokens=4000,
                )

                # Parse structured output
                data = response.output_parsed

                candidate = Candidate(
                    candidate_id=data["candidate_id"],
                    files=data["files"],
                    tests=data.get("tests", []),
                    notes=data.get("notes", ""),
                    status=CandidateStatus.GENERATED,
                )

                candidates.append(candidate)
                print(f"  ✅ Generated candidate {candidate.candidate_id}")

            except Exception as e:
                print(f"  ❌ Failed to generate candidate {i+1}: {e}")

        return candidates

    def _build_candidate_prompt(
        self, task: str, spec: str, design_lever: str, candidate_num: int
    ) -> str:
        """Build prompt for candidate generation."""

        return f"""Generate candidate solution #{candidate_num} for the following task.

TASK: {task}

SPECIFICATION: {spec}

DESIGN APPROACH: Use {design_lever}

REQUIREMENTS:
- Generate ONLY the requested code and tests
- Keep each file ≤ {self.config.max_file_lines} lines
- Use strict JSON format with no prose
- Focus on {design_lever} principles
- Ensure code is production-ready
- Include comprehensive tests
- Follow Python best practices

OUTPUT FORMAT:
{{
  "candidate_id": "c{candidate_num}",
  "files": [
    {{"path": "main.py", "content": "..."}},
    {{"path": "utils.py", "content": "..."}}
  ],
  "tests": [
    {{"path": "test_main.py", "content": "..."}},
    {{"path": "test_utils.py", "content": "..."}}
  ],
  "notes": "Brief design notes (max 100 chars)"
}}

IMPORTANT: Return ONLY valid JSON. No explanations or markdown."""

    async def _pre_gate_candidates(
        self, candidates: list[Candidate]
    ) -> list[Candidate]:
        """Pre-gate candidates with cheap mechanical checks."""

        viable_candidates = []

        for candidate in candidates:
            try:
                # Check AST parse for all Python files
                for file_info in candidate.files + candidate.tests:
                    if file_info["path"].endswith(".py"):
                        ast.parse(file_info["content"])

                # Check file size limits
                oversized_files = []
                for file_info in candidate.files + candidate.tests:
                    lines = len(file_info["content"].split("\n"))
                    if lines > self.config.max_file_lines:
                        oversized_files.append(file_info["path"])

                if oversized_files:
                    print(
                        f"  ⚠️ Candidate {candidate.candidate_id}: Files too large: {oversized_files}"
                    )
                    continue

                candidate.status = CandidateStatus.PRE_GATED
                viable_candidates.append(candidate)
                print(f"  ✅ Candidate {candidate.candidate_id} passed pre-gating")

            except SyntaxError as e:
                print(
                    f"  ❌ Candidate {candidate.candidate_id}: Syntax error in {e.filename}: {e}"
                )
            except Exception as e:
                print(f"  ❌ Candidate {candidate.candidate_id}: Pre-gating failed: {e}")

        return viable_candidates

    async def _run_critics_parallel(
        self, candidates: list[Candidate], spec: str, session_id: str
    ) -> dict[str, list[dict]]:
        """Run critics in parallel for all candidates."""

        critic_types = [
            "contracts",
            "tests",
            "security",
            "performance",
            "style",
            "docs",
        ]
        all_critic_tasks = []

        # Create tasks for all critic-candidate combinations
        for candidate in candidates:
            for critic_type in critic_types:
                task = self._run_single_critic(critic_type, candidate, spec, session_id)
                all_critic_tasks.append(task)

        # Run all critics in parallel
        critic_results = await asyncio.gather(*all_critic_tasks, return_exceptions=True)

        # Organize results by candidate
        results_by_candidate = defaultdict(list)
        task_index = 0

        for candidate in candidates:
            for critic_type in critic_types:
                result = critic_results[task_index]
                task_index += 1

                if isinstance(result, Exception):
                    print(
                        f"  ❌ Critic {critic_type} failed for {candidate.candidate_id}: {result}"
                    )
                    continue

                if result and result.get("status") == "success":
                    results_by_candidate[candidate.candidate_id].append(result["data"])
                    print(
                        f"  ✅ {critic_type} critic completed for {candidate.candidate_id}"
                    )

        return dict(results_by_candidate)

    async def _run_single_critic(
        self, critic_type: str, candidate: Candidate, spec: str, session_id: str
    ) -> dict[str, Any]:
        """Run a single critic on a single candidate."""

        # Build critic-specific prompt
        prompt = self._build_critic_prompt(critic_type, candidate, spec)

        try:
            response = self.client.responses.create(
                model="o3",
                input=[{"role": "developer", "content": prompt}],
                response={
                    "modalities": ["text"],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "json_schema": self.critic_schema,
                        }
                    },
                },
                reasoning={"effort": "low"},
                temperature=0.0,
                max_output_tokens=800,
            )

            # Parse structured output
            data = response.output_parsed

            return {"status": "success", "data": data}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _build_critic_prompt(
        self, critic_type: str, candidate: Candidate, spec: str
    ) -> str:
        """Build critic-specific prompt."""

        # Combine all code into single block for analysis
        all_code = ""
        for file_info in candidate.files + candidate.tests:
            all_code += f"\n# {file_info['path']}\n{file_info['content']}\n"

        base_prompt = f"""You are the {critic_type.upper()} CRITIC. Analyze the following candidate solution.

CANDIDATE ID: {candidate.candidate_id}

ORIGINAL SPECIFICATION:
{spec}

CODE TO ANALYZE:
{all_code}

CRITIC CHARTER:
"""

        # Add critic-specific guidance
        if critic_type == "contracts":
            base_prompt += """- Verify function/class names & argument lists match specification exactly
- Check for signature mismatches, missing parameters, wrong return types
- Produce exact diffs: "got: func(x, y) vs expected: func(x, y, z)"
- Block on any contract violation
- Evidence: exact function signatures, parameter lists, return types"""
        elif critic_type == "tests":
            base_prompt += """- Identify failing tests and missing test coverage
- Output failing test names + assertion lines
- Check if code handles edge cases and error conditions
- Propose ONE minimal test if coverage gap exists
- Evidence: test file names, assertion lines, error messages"""
        elif critic_type == "security":
            base_prompt += """- Check for secrets, unsafe subprocess calls, deserialization issues
- Look for injection vulnerabilities, unsafe file operations
- Verify proper input validation and sanitization
- Evidence: exact code lines with security issues"""
        elif critic_type == "performance":
            base_prompt += """- Identify big-O hotspots, needless copies, inefficient algorithms
- Check for memory leaks, excessive allocations
- Only suggest safe micro-fixes
- Evidence: specific performance bottlenecks"""
        elif critic_type == "style":
            base_prompt += """- Check ruff/mypy alignment, code formatting
- Verify naming conventions, documentation standards
- Block only if parse/type errors exist
- Evidence: specific style violations"""
        elif critic_type == "docs":
            base_prompt += """- Check for missing docstrings, unclear comments
- Verify README updates, API documentation
- Ensure examples are current and working
- Evidence: missing documentation sections"""

        base_prompt += """

IMPORTANT:
- Provide concrete evidence, not vague suggestions
- Use exact line numbers, function names, error messages
- No chain-of-thought - just facts and evidence
- Be specific and actionable in next_actions
- Focus on your charter area only

OUTPUT: Return structured JSON with candidate_id, verdict, scores, failures, and next_actions."""

        return base_prompt

    def _consolidate_and_select(
        self, candidates: list[Candidate], critic_results: dict[str, list[dict]]
    ) -> dict[str, Any]:
        """Consolidate critic results and select winner."""

        blocking_categories = {"syntax", "test", "contract", "security"}

        # Process critic results for each candidate
        candidate_summaries = []

        for candidate in candidates:
            if candidate.candidate_id not in critic_results:
                continue

            # Aggregate scores and failures
            scores = defaultdict(list)
            all_failures = []
            all_actions = []

            for critic_result in critic_results[candidate.candidate_id]:
                for dimension, score in critic_result["scores"].items():
                    scores[dimension].append(float(score))
                all_failures.extend(critic_result["failures"])
                all_actions.extend(critic_result["next_actions"])

            # Calculate average scores (pessimistic for blocking dimensions)
            avg_scores = {}
            for dimension, score_list in scores.items():
                if dimension in ["correctness", "consistency", "safety"]:
                    avg_scores[dimension] = min(score_list)  # Pessimistic
                else:
                    avg_scores[dimension] = sum(score_list) / len(score_list)

            # Calculate weighted score
            weighted_score = (
                0.5 * avg_scores.get("correctness", 0)
                + 0.2 * avg_scores.get("consistency", 0)
                + 0.2 * avg_scores.get("safety", 0)
                + 0.05 * avg_scores.get("efficiency", 0)
                + 0.05 * avg_scores.get("clarity", 0)
            )

            # Identify blocking failures
            blocking_failures = [
                failure
                for failure in all_failures
                if failure["category"] in blocking_categories
            ]

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

            summary = {
                "candidate_id": candidate.candidate_id,
                "scores": avg_scores,
                "blocking_failures": blocking_failures,
                "weighted_score": weighted_score,
                "next_actions": dedup_actions,
                "all_failures": all_failures,
            }

            candidate_summaries.append(summary)

        # Select winner and runner-up
        if not candidate_summaries:
            return {"winner": None, "runner_up": None, "all_summaries": []}

        # Sort by (no blockers, weighted score)
        candidate_summaries.sort(
            key=lambda s: (len(s["blocking_failures"]) == 0, s["weighted_score"]),
            reverse=True,
        )

        winner = candidate_summaries[0]
        runner_up = candidate_summaries[1] if len(candidate_summaries) > 1 else None

        # Collect all actions for synthesis
        all_actions = []
        for summary in candidate_summaries:
            all_actions.extend(summary["next_actions"])

        # De-duplicate all actions
        seen_all_actions = set()
        dedup_all_actions = []
        for action in all_actions:
            key = action.strip().lower()
            if key not in seen_all_actions:
                seen_all_actions.add(key)
                dedup_all_actions.append(action)

        return {
            "winner": winner,
            "runner_up": runner_up,
            "all_summaries": candidate_summaries,
            "all_critic_actions": dedup_all_actions,
        }

    async def _synthesize_improvements(
        self,
        winner: dict,
        runner_up: dict | None,
        all_actions: list[str],
        session_id: str,
    ) -> dict | None:
        """Synthesize improvements using o3."""

        if not winner:
            return None

        # Find the actual candidate objects
        winner_candidate = None
        runner_up_candidate = None

        for candidate in self.sessions[session_id].get("candidates", {}).values():
            if candidate.candidate_id == winner["candidate_id"]:
                winner_candidate = candidate
            elif runner_up and candidate.candidate_id == runner_up["candidate_id"]:
                runner_up_candidate = candidate

        if not winner_candidate:
            return None

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            winner_candidate, runner_up_candidate, all_actions
        )

        try:
            response = self.client.responses.create(
                model="o3",
                input=[{"role": "developer", "content": prompt}],
                response={
                    "modalities": ["text"],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "json_schema": self.synthesis_schema,
                        }
                    },
                },
                reasoning={"effort": "medium"},
                temperature=0.0,
                max_output_tokens=2000,
            )

            # Parse structured output
            data = response.output_parsed

            return {
                "files": data["files"],
                "tests": data["tests"],
                "changes_made": data["changes_made"],
            }

        except Exception as e:
            print(f"  ❌ Synthesis failed: {e}")
            return None

    def _build_synthesis_prompt(
        self, winner: Candidate, runner_up: Candidate | None, all_actions: list[str]
    ) -> str:
        """Build prompt for synthesis."""

        # Combine winner code
        winner_code = ""
        for file_info in winner.files + winner.tests:
            winner_code += f"\n# {file_info['path']}\n{file_info['content']}\n"

        # Combine runner-up code (if available)
        runner_up_code = ""
        if runner_up:
            for file_info in runner_up.files + runner_up.tests:
                runner_up_code += f"\n# {file_info['path']}\n{file_info['content']}\n"

        prompt = f"""You are the SYNTHESIZER. Improve the winning candidate by incorporating the best parts of the runner-up and addressing all critic feedback.

WINNING CANDIDATE ({winner.candidate_id}):
{winner_code}

"""

        if runner_up:
            prompt += f"""RUNNER-UP CANDIDATE ({runner_up.candidate_id}):
{runner_up_code}

"""

        prompt += f"""CRITIC FEEDBACK TO ADDRESS:
{chr(10).join(f"- {action}" for action in all_actions[:10])}

TASK:
- Combine the best parts of both candidates
- Address all critic feedback systematically
- Make minimal, focused changes
- Ensure code remains production-ready
- Keep each file ≤ {self.config.max_file_lines} lines

OUTPUT: Return structured JSON with improved files, tests, and description of changes made.

IMPORTANT: Focus on the most critical improvements first. Don't try to address every minor issue."""

        return prompt


# Example usage
async def main():
    """Example of multi-candidate tournament."""

    tournament = MultiCandidateTournament(TournamentConfig(num_candidates=3))

    # Example task
    task = """Create a simple email validation function with comprehensive error handling."""

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
    """

    # Run tournament
    print("🏆 Starting Multi-Candidate Tournament")
    result = await tournament.run_tournament(
        task=task, spec=spec, session_id="tournament_001"
    )

    # Display results
    print("\n" + "=" * 60)
    print("🎯 TOURNAMENT RESULTS")
    print("=" * 60)

    if result["winner"]:
        print(f"🏆 Winner: {result['winner']['candidate_id']}")
        print(f"  Weighted Score: {result['winner']['weighted_score']:.3f}")
        print(f"  Blocking Failures: {len(result['winner']['blocking_failures'])}")
        print(f"  Scores: {result['winner']['scores']}")

        if result["runner_up"]:
            print(f"🥈 Runner-up: {result['runner_up']['candidate_id']}")
            print(f"  Weighted Score: {result['runner_up']['weighted_score']:.3f}")

        if result.get("improved_winner"):
            print(
                f"🔧 Improved winner synthesized with {result['improved_winner']['changes_made']}"
            )

    print("\nAll Candidates:")
    for summary in result["all_summaries"]:
        status = "✅" if len(summary["blocking_failures"]) == 0 else "⚠️"
        print(
            f"  {status} {summary['candidate_id']}: {summary['weighted_score']:.3f} "
            f"(blockers: {len(summary['blocking_failures'])})"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
