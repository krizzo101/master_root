"""Error pattern learning for automatic recovery."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ErrorPattern:
    """Error pattern with solutions."""

    error_signature: str
    error_type: str
    pattern: str
    solutions: List[Dict[str, Any]]
    first_seen: str
    last_seen: str
    occurrences: int


@dataclass
class Solution:
    """Solution for an error pattern."""

    fix: str
    success_rate: float
    code_snippet: Optional[str]
    attempts: int = 0
    successes: int = 0


class ErrorPatternLearner:
    """Learn from errors and suggest solutions."""

    def __init__(self, cache_path: str = ".proj-intel/error_patterns.json"):
        """Initialize error learner."""
        self.cache_path = Path(cache_path)
        self.patterns: Dict[str, ErrorPattern] = {}
        self._logger = logger.bind(component="ErrorPatternLearner")
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load error patterns from cache."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r") as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = ErrorPattern(**pattern_data)
                        self.patterns[pattern.error_signature] = pattern
                self._logger.info(f"Loaded {len(self.patterns)} error patterns")
            except Exception as e:
                self._logger.error(f"Failed to load error patterns: {e}")

    def _save_patterns(self) -> None:
        """Save error patterns to cache."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = [asdict(pattern) for pattern in self.patterns.values()]
            with open(self.cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save error patterns: {e}")

    def _generate_signature(self, error: Exception) -> str:
        """Generate unique signature for error."""
        error_str = f"{type(error).__name__}:{str(error)}"
        return hashlib.md5(error_str.encode()).hexdigest()[:16]

    def record_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        solution: Dict[str, Any] = None,
    ) -> str:
        """Record an error occurrence."""
        signature = self._generate_signature(error)
        timestamp = datetime.now().isoformat()

        if signature in self.patterns:
            # Update existing pattern
            pattern = self.patterns[signature]
            pattern.last_seen = timestamp
            pattern.occurrences += 1

            # Add solution if provided
            if solution:
                # Check if solution already exists
                existing = False
                for sol in pattern.solutions:
                    if sol["fix"] == solution.get("fix"):
                        existing = True
                        break

                if not existing:
                    pattern.solutions.append(solution)
        else:
            # Create new pattern
            pattern = ErrorPattern(
                error_signature=signature,
                error_type=type(error).__name__,
                pattern=str(error),
                solutions=[solution] if solution else [],
                first_seen=timestamp,
                last_seen=timestamp,
                occurrences=1,
            )
            self.patterns[signature] = pattern

        self._save_patterns()
        self._logger.info(f"Recorded error pattern: {signature}")
        return signature

    def get_solutions(self, error: Exception) -> List[Dict[str, Any]]:
        """Get solutions for an error."""
        signature = self._generate_signature(error)

        if signature in self.patterns:
            pattern = self.patterns[signature]
            # Sort solutions by success rate
            solutions = sorted(
                pattern.solutions, key=lambda s: s.get("success_rate", 0), reverse=True
            )
            self._logger.info(f"Found {len(solutions)} solutions for error {signature}")
            return solutions

        return []

    def update_solution_success(
        self, error: Exception, solution_fix: str, success: bool
    ) -> None:
        """Update solution success rate."""
        signature = self._generate_signature(error)

        if signature in self.patterns:
            pattern = self.patterns[signature]
            for solution in pattern.solutions:
                if solution.get("fix") == solution_fix:
                    attempts = solution.get("attempts", 0) + 1
                    successes = solution.get("successes", 0) + (1 if success else 0)
                    solution["attempts"] = attempts
                    solution["successes"] = successes
                    solution["success_rate"] = (
                        successes / attempts if attempts > 0 else 0
                    )
                    break

            self._save_patterns()

    def get_statistics(self) -> Dict[str, Any]:
        """Get error pattern statistics."""
        total_patterns = len(self.patterns)
        total_occurrences = sum(p.occurrences for p in self.patterns.values())
        total_solutions = sum(len(p.solutions) for p in self.patterns.values())

        # Find most common errors
        most_common = sorted(
            self.patterns.values(), key=lambda p: p.occurrences, reverse=True
        )[:5]

        return {
            "total_patterns": total_patterns,
            "total_occurrences": total_occurrences,
            "total_solutions": total_solutions,
            "most_common": [
                {
                    "type": p.error_type,
                    "occurrences": p.occurrences,
                    "solutions": len(p.solutions),
                }
                for p in most_common
            ],
        }

    def clear_old_patterns(self, days: int = 30) -> int:
        """Clear patterns older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = 0

        for signature in list(self.patterns.keys()):
            pattern = self.patterns[signature]
            last_seen = datetime.fromisoformat(pattern.last_seen).timestamp()
            if last_seen < cutoff:
                del self.patterns[signature]
                removed += 1

        if removed > 0:
            self._save_patterns()
            self._logger.info(f"Removed {removed} old error patterns")

        return removed


# Global learner instance
learner = ErrorPatternLearner()
