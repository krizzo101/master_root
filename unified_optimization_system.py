#!/usr/bin/env python3
"""
Unified Optimization System

Parameter-driven system that selects the right optimization level:
- Fast Mode: Single-shot GPT-5 (30s, $0.05)
- Standard Mode: Multi-critic (3min, $0.15)
- Tournament Mode: K-candidates + critics (12min, $0.36)
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI
import os


class OptimizationLevel(Enum):
    FAST = "fast"
    STANDARD = "standard"
    TOURNAMENT = "tournament"


@dataclass
class OptimizationRequest:
    """Request configuration for optimization."""

    task: str
    spec: str = ""
    optimization_level: str = "auto"  # "fast", "standard", "tournament", "auto"
    max_time: Optional[int] = None  # seconds
    max_cost: Optional[float] = None  # dollars
    quality_priority: str = "balanced"  # "speed", "balanced", "quality"


@dataclass
class FastModeConfig:
    """Configuration for fast mode (single-shot)."""

    model: str = "gpt-5-nano"
    verbosity: str = "low"
    max_output_tokens: int = 2000
    temperature: float = 0.0
    enable_critic: bool = False
    enable_structured_output: bool = True


@dataclass
class StandardModeConfig:
    """Configuration for standard mode (multi-critic)."""

    model: str = "gpt-5-nano"
    verbosity: str = "medium"
    max_output_tokens: int = 4000
    temperature: float = 0.0
    enable_critic: bool = True
    critic_types: List[str] = field(
        default_factory=lambda: ["contracts", "tests", "security"]
    )
    max_iterations: int = 3
    enable_structured_output: bool = True


@dataclass
class TournamentModeConfig:
    """Configuration for tournament mode (K-candidates)."""

    num_candidates: int = 3
    max_file_lines: int = 200
    temperature_range: Tuple[float, float] = (0.1, 0.2)
    enable_pre_gating: bool = True
    enable_synthesis: bool = True
    max_iterations: int = 3
    critic_types: List[str] = field(
        default_factory=lambda: [
            "contracts",
            "tests",
            "security",
            "performance",
            "style",
            "docs",
        ]
    )


class UnifiedOptimizationSystem:
    """
    Unified system that selects and executes the appropriate optimization level.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sessions = {}

        # Import optimization systems
        try:
            from multi_critic_system import MultiCriticSystem
            from multi_candidate_tournament import MultiCandidateTournament

            self.multi_critic = MultiCriticSystem()
            self.tournament = MultiCandidateTournament()
        except ImportError:
            print("⚠️ Multi-critic and tournament systems not available")
            self.multi_critic = None
            self.tournament = None

    def select_optimization_level(
        self, request: OptimizationRequest
    ) -> OptimizationLevel:
        """Automatically select optimization level based on task characteristics."""

        if request.optimization_level != "auto":
            return OptimizationLevel(request.optimization_level)

        # Analyze task complexity
        complexity_score = self._analyze_task_complexity(request.task, request.spec)

        # Check for high-stakes indicators
        high_stakes_indicators = [
            "architecture",
            "design",
            "system",
            "performance",
            "security",
            "production",
            "critical",
            "optimization",
            "scalability",
        ]

        has_high_stakes = any(
            indicator in request.task.lower() for indicator in high_stakes_indicators
        )

        # Check for multiple approaches
        has_multiple_approaches = any(
            phrase in request.task.lower()
            for phrase in [
                "different approaches",
                "multiple ways",
                "various strategies",
                "compare",
                "evaluate",
                "choose between",
            ]
        )

        # Check constraints
        if request.max_time and request.max_time < 120:  # Less than 2 minutes
            return OptimizationLevel.FAST
        if request.max_cost and request.max_cost < 0.10:  # Less than 10 cents
            return OptimizationLevel.FAST
        if request.quality_priority == "speed":
            return OptimizationLevel.FAST
        if request.quality_priority == "quality":
            return OptimizationLevel.TOURNAMENT

        # Decision logic
        if complexity_score < 3 and not has_high_stakes:
            return OptimizationLevel.FAST
        elif complexity_score >= 7 or has_high_stakes or has_multiple_approaches:
            return OptimizationLevel.TOURNAMENT
        else:
            return OptimizationLevel.STANDARD

    def _analyze_task_complexity(self, task: str, spec: str) -> int:
        """Analyze task complexity on scale 1-10."""
        score = 1

        # File count estimation
        if "multiple files" in task or "module" in task:
            score += 2
        if "class" in task or "interface" in task:
            score += 1
        if "test" in task or "testing" in task:
            score += 1
        if "api" in task or "endpoint" in task:
            score += 1
        if "database" in task or "persistence" in task:
            score += 1
        if "async" in task or "concurrent" in task:
            score += 1
        if "security" in task or "authentication" in task:
            score += 1
        if "performance" in task or "optimization" in task:
            score += 1

        return min(score, 10)

    async def optimize(self, request: OptimizationRequest) -> Dict[str, Any]:
        """
        Main entry point - selects and executes appropriate optimization level.

        Args:
            request: Optimization request with task, spec, and preferences

        Returns:
            Optimization result with code, metrics, and metadata
        """

        # Select optimization level
        level = self.select_optimization_level(request)
        print(f"🎯 Selected optimization level: {level.value.upper()}")

        # Execute appropriate optimization
        if level == OptimizationLevel.FAST:
            return await self._execute_fast_mode(request)
        elif level == OptimizationLevel.STANDARD:
            return await self._execute_standard_mode(request)
        elif level == OptimizationLevel.TOURNAMENT:
            return await self._execute_tournament_mode(request)
        else:
            raise ValueError(f"Unknown optimization level: {level}")

    async def _execute_fast_mode(self, request: OptimizationRequest) -> Dict[str, Any]:
        """Execute fast mode optimization (single-shot GPT-5)."""

        config = FastModeConfig()

        # Build prompt
        prompt = self._build_fast_mode_prompt(request.task, request.spec)

        # Get structured output schema
        schema = self._get_fast_mode_schema()

        try:
            response = self.client.responses.create(
                model=config.model,
                input=[{"role": "developer", "content": prompt}],
                response={
                    "modalities": ["text"],
                    "text": {"format": {"type": "json_schema", "json_schema": schema}},
                },
                temperature=config.temperature,
                max_output_tokens=config.max_output_tokens,
            )

            # Parse structured output
            data = response.output_parsed

            # Basic validation
            validation_result = self._validate_fast_mode_result(data)

            return {
                "optimization_level": "fast",
                "status": "success",
                "files": data.get("files", []),
                "tests": data.get("tests", []),
                "commands": data.get("commands", []),
                "explanation": data.get("explanation", ""),
                "validation": validation_result,
                "metrics": {
                    "time_seconds": 30,  # Estimated
                    "cost_dollars": 0.05,  # Estimated
                    "tokens_used": response.usage.total_tokens
                    if hasattr(response, "usage")
                    else 0,
                },
            }

        except Exception as e:
            return {
                "optimization_level": "fast",
                "status": "error",
                "error": str(e),
                "metrics": {"time_seconds": 30, "cost_dollars": 0.05, "tokens_used": 0},
            }

    async def _execute_standard_mode(
        self, request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Execute standard mode optimization (multi-critic)."""

        if not self.multi_critic:
            return {
                "optimization_level": "standard",
                "status": "error",
                "error": "Multi-critic system not available",
            }

        config = StandardModeConfig()

        # Start session
        session_id = f"standard_{hash(request.task) % 10000}"
        self.multi_critic.start_session(session_id)

        try:
            # Generate initial code with main agent
            initial_code = await self._generate_initial_code(
                request.task, request.spec, config
            )

            # Run multi-critic analysis
            critic_result = await self.multi_critic.analyze_code(
                code=initial_code, spec=request.spec, session_id=session_id, iteration=1
            )

            # Apply critic feedback if needed
            final_code = initial_code
            if critic_result.verdict == "revise" and critic_result.next_actions:
                final_code = await self._apply_critic_fixes(
                    initial_code, critic_result.next_actions
                )

            return {
                "optimization_level": "standard",
                "status": "success",
                "files": [{"path": "main.py", "content": final_code}],
                "tests": [],
                "commands": [],
                "explanation": f"Generated with {len(critic_result.next_actions)} critic suggestions",
                "critic_result": {
                    "verdict": critic_result.verdict,
                    "scores": critic_result.scores,
                    "next_actions": critic_result.next_actions,
                },
                "metrics": {
                    "time_seconds": 180,  # Estimated
                    "cost_dollars": 0.15,  # Estimated
                    "total_critics": critic_result.total_critics,
                },
            }

        except Exception as e:
            return {
                "optimization_level": "standard",
                "status": "error",
                "error": str(e),
                "metrics": {
                    "time_seconds": 180,
                    "cost_dollars": 0.15,
                    "total_critics": 0,
                },
            }

    async def _execute_tournament_mode(
        self, request: OptimizationRequest
    ) -> Dict[str, Any]:
        """Execute tournament mode optimization (K-candidates + critics)."""

        if not self.tournament:
            return {
                "optimization_level": "tournament",
                "status": "error",
                "error": "Tournament system not available",
            }

        config = TournamentModeConfig()

        # Start tournament session
        session_id = f"tournament_{hash(request.task) % 10000}"
        self.tournament.start_tournament(session_id)

        try:
            # Run tournament
            tournament_result = await self.tournament.run_tournament(
                task=request.task, spec=request.spec, session_id=session_id
            )

            # Extract winner
            winner = tournament_result.get("winner")
            if not winner:
                return {
                    "optimization_level": "tournament",
                    "status": "error",
                    "error": "No viable candidates found",
                }

            # Get improved winner if available
            improved_winner = tournament_result.get("improved_winner")
            final_files = improved_winner["files"] if improved_winner else []

            return {
                "optimization_level": "tournament",
                "status": "success",
                "files": final_files,
                "tests": [],
                "commands": [],
                "explanation": f"Tournament winner: {winner['candidate_id']} (score: {winner['weighted_score']:.3f})",
                "tournament_result": {
                    "winner": winner,
                    "runner_up": tournament_result.get("runner_up"),
                    "all_candidates": len(tournament_result.get("all_summaries", [])),
                    "all_actions": tournament_result.get("all_critic_actions", []),
                },
                "metrics": {
                    "time_seconds": 720,  # Estimated
                    "cost_dollars": 0.36,  # Estimated
                    "candidates_generated": config.num_candidates,
                    "critics_used": len(config.critic_types),
                },
            }

        except Exception as e:
            return {
                "optimization_level": "tournament",
                "status": "error",
                "error": str(e),
                "metrics": {
                    "time_seconds": 720,
                    "cost_dollars": 0.36,
                    "candidates_generated": 0,
                    "critics_used": 0,
                },
            }

    def _build_fast_mode_prompt(self, task: str, spec: str) -> str:
        """Build prompt for fast mode."""

        return f"""Generate code for the following task.

TASK: {task}

SPECIFICATION: {spec}

REQUIREMENTS:
- Generate production-ready code
- Include comprehensive tests
- Follow Python best practices
- Use type hints
- Add proper documentation
- Handle edge cases and errors

OUTPUT FORMAT:
{{
  "files": [
    {{"path": "main.py", "content": "..."}},
    {{"path": "utils.py", "content": "..."}}
  ],
  "tests": [
    {{"path": "test_main.py", "content": "..."}},
    {{"path": "test_utils.py", "content": "..."}}
  ],
  "commands": ["pip install pytest", "python -m pytest"],
  "explanation": "Brief explanation of the solution"
}}

IMPORTANT: Return ONLY valid JSON. No explanations or markdown."""

    def _get_fast_mode_schema(self) -> Dict[str, Any]:
        """Get structured output schema for fast mode."""
        return {
            "name": "fast_mode_result",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["files"],
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
                    "commands": {"type": "array", "items": {"type": "string"}},
                    "explanation": {"type": "string"},
                },
            },
            "strict": True,
        }

    def _validate_fast_mode_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate fast mode result."""
        validation = {
            "syntax_valid": True,
            "files_count": len(data.get("files", [])),
            "tests_count": len(data.get("tests", [])),
            "errors": [],
        }

        # Check syntax for Python files
        for file_info in data.get("files", []) + data.get("tests", []):
            if file_info["path"].endswith(".py"):
                try:
                    import ast

                    ast.parse(file_info["content"])
                except SyntaxError as e:
                    validation["syntax_valid"] = False
                    validation["errors"].append(
                        f"Syntax error in {file_info['path']}: {e}"
                    )

        return validation

    async def _generate_initial_code(
        self, task: str, spec: str, config: StandardModeConfig
    ) -> str:
        """Generate initial code for standard mode."""

        prompt = f"""Generate initial code for the following task.

TASK: {task}

SPECIFICATION: {spec}

REQUIREMENTS:
- Generate production-ready code
- Include comprehensive tests
- Follow Python best practices
- Use type hints
- Add proper documentation
- Handle edge cases and errors

Return the main code file content only (no JSON wrapper)."""

        try:
            response = self.client.responses.create(
                model=config.model,
                input=[{"role": "developer", "content": prompt}],
                temperature=config.temperature,
                max_output_tokens=config.max_output_tokens,
            )

            return response.output_text

        except Exception as e:
            return f"# Error generating code: {e}\n\ndef placeholder():\n    pass"

    async def _apply_critic_fixes(self, code: str, actions: List[str]) -> str:
        """Apply critic-suggested fixes to code."""

        prompt = f"""Apply the following fixes to the code:

CODE:
{code}

FIXES TO APPLY:
{chr(10).join(f"- {action}" for action in actions[:5])}

Return the improved code only (no JSON wrapper)."""

        try:
            response = self.client.responses.create(
                model="gpt-5-nano",
                input=[{"role": "developer", "content": prompt}],
                temperature=0.0,
                max_output_tokens=4000,
            )

            return response.output_text

        except Exception as e:
            return code  # Return original code if fixes fail


# Example usage
async def main():
    """Example of unified optimization system."""

    system = UnifiedOptimizationSystem()

    # Example requests
    requests = [
        # Fast mode example
        OptimizationRequest(
            task="Fix the syntax error in line 45 of utils.py",
            optimization_level="fast",
        ),
        # Standard mode example
        OptimizationRequest(
            task="Create a user authentication system with JWT tokens",
            spec="Must support login, logout, token refresh, and role-based access",
            optimization_level="standard",
        ),
        # Tournament mode example
        OptimizationRequest(
            task="Design a scalable microservices architecture for e-commerce platform",
            spec="Must handle 10k concurrent users, support multiple payment gateways, and be cloud-native",
            optimization_level="tournament",
        ),
        # Auto-selection example
        OptimizationRequest(
            task="Add input validation to the user registration function",
            optimization_level="auto",
        ),
    ]

    for i, request in enumerate(requests, 1):
        print(f"\n{'='*60}")
        print(f"REQUEST {i}: {request.task[:50]}...")
        print(f"{'='*60}")

        result = await system.optimize(request)

        print(f"Level: {result['optimization_level'].upper()}")
        print(f"Status: {result['status']}")
        print(f"Files: {len(result.get('files', []))}")
        print(f"Time: {result['metrics']['time_seconds']}s")
        print(f"Cost: ${result['metrics']['cost_dollars']:.2f}")

        if result["status"] == "error":
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
