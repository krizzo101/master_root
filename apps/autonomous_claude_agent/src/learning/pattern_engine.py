"""
Pattern Engine - Recognizes and learns patterns from agent interactions
"""

import asyncio
import json
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PatternType(Enum):
    """Types of patterns that can be recognized"""

    TASK_SEQUENCE = "task_sequence"  # Sequence of tasks that often occur together
    ERROR_RECOVERY = "error_recovery"  # How errors are typically resolved
    OPTIMIZATION = "optimization"  # Performance optimization patterns
    TOOL_USAGE = "tool_usage"  # Which tools are used for which tasks
    SUCCESS_PATH = "success_path"  # Successful task completion paths
    FAILURE_MODE = "failure_mode"  # Common failure patterns
    USER_PREFERENCE = "user_preference"  # User-specific preferences
    CONTEXT_SWITCH = "context_switch"  # Context switching patterns


@dataclass
class Pattern:
    """Represents a recognized pattern"""

    id: str
    type: PatternType
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    occurrences: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    def matches(self, context: Dict[str, Any]) -> float:
        """Calculate match score for given context"""
        score = 0.0

        # Check trigger conditions
        for condition in self.trigger_conditions:
            if self._evaluate_condition(condition, context):
                score += 1.0

        if self.trigger_conditions:
            score = score / len(self.trigger_conditions)

        # Weight by confidence and success rate
        score *= self.confidence * self.success_rate

        return score

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition against context"""
        try:
            # Simple keyword matching for now
            # In production, this would be more sophisticated
            condition_lower = condition.lower()
            context_str = json.dumps(context).lower()
            return condition_lower in context_str
        except:
            return False


class PatternEngine:
    """Engine for recognizing and learning patterns"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.patterns: Dict[str, Pattern] = {}
        self.pattern_index: Dict[PatternType, Set[str]] = defaultdict(set)
        self.sequence_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000
        self.cache_dir = cache_dir or Path.home() / ".autonomous_claude" / "patterns"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ML components
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.pattern_vectors = None
        self.pattern_ids = []

        # Statistics
        self.pattern_stats = defaultdict(
            lambda: {"triggers": 0, "successes": 0, "failures": 0, "total_time": 0.0}
        )

        self._lock = asyncio.Lock()
        self._load_patterns()

    def _load_patterns(self):
        """Load patterns from cache"""
        pattern_file = self.cache_dir / "patterns.pkl"
        if pattern_file.exists():
            try:
                with open(pattern_file, "rb") as f:
                    data = pickle.load(f)
                    self.patterns = data.get("patterns", {})
                    self.pattern_stats = data.get(
                        "stats",
                        defaultdict(
                            lambda: {
                                "triggers": 0,
                                "successes": 0,
                                "failures": 0,
                                "total_time": 0.0,
                            }
                        ),
                    )
                    self._rebuild_index()
                    logger.info(f"Loaded {len(self.patterns)} patterns from cache")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")

    def _save_patterns(self):
        """Save patterns to cache"""
        pattern_file = self.cache_dir / "patterns.pkl"
        try:
            data = {"patterns": self.patterns, "stats": dict(self.pattern_stats)}
            with open(pattern_file, "wb") as f:
                pickle.dump(data, f)
            logger.debug("Patterns saved to cache")
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")

    def _rebuild_index(self):
        """Rebuild pattern index"""
        self.pattern_index.clear()
        for pattern_id, pattern in self.patterns.items():
            self.pattern_index[pattern.type].add(pattern_id)

    async def observe_interaction(self, interaction: Dict[str, Any]):
        """Observe an interaction for pattern learning"""
        async with self._lock:
            # Add to sequence buffer
            self.sequence_buffer.append({"timestamp": datetime.now(), "interaction": interaction})

            # Trim buffer if too large
            if len(self.sequence_buffer) > self.max_buffer_size:
                self.sequence_buffer = self.sequence_buffer[-self.max_buffer_size :]

            # Try to extract patterns
            await self._extract_patterns(interaction)

            # Match against existing patterns
            matches = await self.find_matching_patterns(interaction)

            # Update pattern statistics
            for pattern_id, score in matches:
                self.pattern_stats[pattern_id]["triggers"] += 1

    async def _extract_patterns(self, interaction: Dict[str, Any]):
        """Extract patterns from recent interactions"""

        # Look for sequences in buffer
        if len(self.sequence_buffer) >= 3:
            await self._extract_sequence_patterns()

        # Look for error recovery patterns
        if interaction.get("error"):
            await self._extract_error_patterns(interaction)

        # Look for tool usage patterns
        if interaction.get("tool_used"):
            await self._extract_tool_patterns(interaction)

        # Look for optimization opportunities
        if interaction.get("execution_time"):
            await self._extract_optimization_patterns(interaction)

    async def _extract_sequence_patterns(self):
        """Extract sequence patterns from buffer"""

        # Look at last N interactions
        recent = self.sequence_buffer[-10:]

        # Extract task sequence
        tasks = [
            item["interaction"].get("task", "")
            for item in recent
            if item["interaction"].get("task")
        ]

        if len(tasks) >= 3:
            # Look for repeated sequences
            for i in range(len(tasks) - 2):
                sequence = tasks[i : i + 3]
                sequence_key = " -> ".join(sequence)

                # Check if this sequence appears multiple times
                count = self._count_sequence(sequence)

                if count >= 2:
                    pattern_id = f"seq_{hash(sequence_key) % 1000000}"

                    if pattern_id not in self.patterns:
                        pattern = Pattern(
                            id=pattern_id,
                            type=PatternType.TASK_SEQUENCE,
                            description=f"Task sequence: {sequence_key}",
                            trigger_conditions=[sequence[0]],
                            actions=sequence[1:],
                            confidence=min(count / 10.0, 1.0),
                            occurrences=count,
                        )

                        await self.register_pattern(pattern)

    def _count_sequence(self, sequence: List[str]) -> int:
        """Count occurrences of a sequence in buffer"""
        count = 0
        buffer_tasks = [
            item["interaction"].get("task", "")
            for item in self.sequence_buffer
            if item["interaction"].get("task")
        ]

        for i in range(len(buffer_tasks) - len(sequence) + 1):
            if buffer_tasks[i : i + len(sequence)] == sequence:
                count += 1

        return count

    async def _extract_error_patterns(self, interaction: Dict[str, Any]):
        """Extract error recovery patterns"""

        error = interaction.get("error")
        recovery = interaction.get("recovery_action")

        if error and recovery:
            pattern_id = f"error_{hash(error) % 1000000}"

            if pattern_id in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pattern_id]
                pattern.occurrences += 1
                if recovery not in pattern.actions:
                    pattern.actions.append(recovery)
            else:
                # Create new pattern
                pattern = Pattern(
                    id=pattern_id,
                    type=PatternType.ERROR_RECOVERY,
                    description=f"Recovery for: {error[:100]}",
                    trigger_conditions=[error],
                    actions=[recovery],
                    confidence=0.5,
                    occurrences=1,
                )

                await self.register_pattern(pattern)

    async def _extract_tool_patterns(self, interaction: Dict[str, Any]):
        """Extract tool usage patterns"""

        task = interaction.get("task", "")
        tool = interaction.get("tool_used", "")
        success = interaction.get("success", False)

        if task and tool:
            pattern_id = f"tool_{hash(f'{task}_{tool}') % 1000000}"

            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                pattern.occurrences += 1
                if success:
                    self.pattern_stats[pattern_id]["successes"] += 1
                pattern.success_rate = (
                    self.pattern_stats[pattern_id]["successes"] / pattern.occurrences
                )
            else:
                pattern = Pattern(
                    id=pattern_id,
                    type=PatternType.TOOL_USAGE,
                    description=f"Use {tool} for {task[:50]}",
                    trigger_conditions=[task],
                    actions=[f"use_tool:{tool}"],
                    confidence=0.7,
                    occurrences=1,
                    success_rate=1.0 if success else 0.0,
                )

                await self.register_pattern(pattern)

    async def _extract_optimization_patterns(self, interaction: Dict[str, Any]):
        """Extract optimization patterns"""

        task = interaction.get("task", "")
        execution_time = interaction.get("execution_time", 0)
        method = interaction.get("method", "")

        if task and execution_time and method:
            # Look for similar tasks with different execution times
            similar_tasks = [
                item for item in self.sequence_buffer if item["interaction"].get("task") == task
            ]

            if len(similar_tasks) >= 2:
                times = [
                    item["interaction"].get("execution_time", float("inf"))
                    for item in similar_tasks
                ]

                avg_time = np.mean([t for t in times if t != float("inf")])

                if execution_time < avg_time * 0.5:  # 50% faster
                    pattern_id = f"opt_{hash(f'{task}_{method}') % 1000000}"

                    pattern = Pattern(
                        id=pattern_id,
                        type=PatternType.OPTIMIZATION,
                        description=f"Fast method for {task[:50]}: {method}",
                        trigger_conditions=[task],
                        actions=[f"method:{method}"],
                        confidence=0.8,
                        occurrences=1,
                        avg_execution_time=execution_time,
                    )

                    await self.register_pattern(pattern)

    async def register_pattern(self, pattern: Pattern) -> bool:
        """Register a new pattern"""
        async with self._lock:
            try:
                # Check for duplicates
                if pattern.id in self.patterns:
                    existing = self.patterns[pattern.id]
                    # Merge patterns
                    existing.occurrences += pattern.occurrences
                    existing.confidence = max(existing.confidence, pattern.confidence)
                    existing.last_used = datetime.now()
                else:
                    # Add new pattern
                    self.patterns[pattern.id] = pattern
                    self.pattern_index[pattern.type].add(pattern.id)

                    # Update vector representation
                    await self._update_pattern_vectors()

                self._save_patterns()
                logger.info(f"Registered pattern: {pattern.id} ({pattern.type.value})")
                return True

            except Exception as e:
                logger.error(f"Failed to register pattern: {e}")
                return False

    async def _update_pattern_vectors(self):
        """Update vector representations of patterns for similarity matching"""

        if not self.patterns:
            return

        try:
            # Create text representations of patterns
            pattern_texts = []
            self.pattern_ids = []

            for pattern_id, pattern in self.patterns.items():
                text = f"{pattern.description} {' '.join(pattern.trigger_conditions)} {' '.join(pattern.actions)}"
                pattern_texts.append(text)
                self.pattern_ids.append(pattern_id)

            # Fit vectorizer and transform patterns
            self.pattern_vectors = self.vectorizer.fit_transform(pattern_texts)

        except Exception as e:
            logger.error(f"Failed to update pattern vectors: {e}")

    async def find_matching_patterns(
        self, context: Dict[str, Any], threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """Find patterns matching the given context"""

        matches = []

        # Convert context to text
        context_text = json.dumps(context)

        # Use vector similarity if available
        if self.pattern_vectors is not None:
            try:
                context_vector = self.vectorizer.transform([context_text])
                similarities = cosine_similarity(context_vector, self.pattern_vectors)[0]

                for i, similarity in enumerate(similarities):
                    if similarity > threshold:
                        pattern_id = self.pattern_ids[i]
                        pattern = self.patterns[pattern_id]

                        # Calculate final score
                        score = similarity * pattern.confidence * pattern.success_rate

                        if score > threshold:
                            matches.append((pattern_id, score))
            except:
                pass

        # Fallback to direct matching
        for pattern_id, pattern in self.patterns.items():
            score = pattern.matches(context)
            if score > threshold:
                matches.append((pattern_id, score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches[:10]  # Return top 10 matches

    async def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get action recommendations based on patterns"""

        recommendations = []
        matches = await self.find_matching_patterns(context)

        for pattern_id, score in matches[:5]:
            pattern = self.patterns[pattern_id]

            recommendation = {
                "pattern_id": pattern_id,
                "type": pattern.type.value,
                "actions": pattern.actions,
                "confidence": score,
                "reasoning": pattern.description,
                "success_rate": pattern.success_rate,
                "avg_time": pattern.avg_execution_time,
            }

            recommendations.append(recommendation)

        return recommendations

    async def update_pattern_outcome(self, pattern_id: str, success: bool, execution_time: float):
        """Update pattern statistics based on outcome"""
        async with self._lock:
            if pattern_id not in self.patterns:
                return

            pattern = self.patterns[pattern_id]
            stats = self.pattern_stats[pattern_id]

            # Update statistics
            if success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1

            stats["total_time"] += execution_time

            # Update pattern metrics
            pattern.last_used = datetime.now()
            pattern.success_rate = stats["successes"] / (stats["successes"] + stats["failures"])
            pattern.avg_execution_time = stats["total_time"] / (
                stats["successes"] + stats["failures"]
            )

            # Adjust confidence based on success rate
            if pattern.occurrences > 5:
                pattern.confidence = min(pattern.success_rate * 1.2, 1.0)

            self._save_patterns()

    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type"""
        pattern_ids = self.pattern_index.get(pattern_type, set())
        return [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]

    async def prune_ineffective_patterns(
        self, min_success_rate: float = 0.3, min_occurrences: int = 5
    ):
        """Remove patterns that are not effective"""
        async with self._lock:
            to_remove = []

            for pattern_id, pattern in self.patterns.items():
                if (
                    pattern.occurrences >= min_occurrences
                    and pattern.success_rate < min_success_rate
                ):
                    to_remove.append(pattern_id)

                # Also remove old unused patterns
                if pattern.last_used:
                    days_unused = (datetime.now() - pattern.last_used).days
                    if days_unused > 30 and pattern.occurrences < 10:
                        to_remove.append(pattern_id)

            for pattern_id in to_remove:
                del self.patterns[pattern_id]
                for pattern_set in self.pattern_index.values():
                    pattern_set.discard(pattern_id)

            if to_remove:
                logger.info(f"Pruned {len(to_remove)} ineffective patterns")
                self._save_patterns()
                await self._update_pattern_vectors()

    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern engine statistics"""

        total_patterns = len(self.patterns)
        by_type = {ptype.value: len(self.pattern_index[ptype]) for ptype in PatternType}

        # Calculate average metrics
        avg_confidence = (
            np.mean([p.confidence for p in self.patterns.values()]) if self.patterns else 0
        )
        avg_success_rate = (
            np.mean([p.success_rate for p in self.patterns.values()]) if self.patterns else 0
        )

        # Find most successful patterns
        successful_patterns = sorted(
            self.patterns.values(), key=lambda p: p.success_rate * p.occurrences, reverse=True
        )[:5]

        return {
            "total_patterns": total_patterns,
            "by_type": by_type,
            "avg_confidence": avg_confidence,
            "avg_success_rate": avg_success_rate,
            "buffer_size": len(self.sequence_buffer),
            "most_successful": [
                {
                    "id": p.id,
                    "type": p.type.value,
                    "description": p.description,
                    "success_rate": p.success_rate,
                    "occurrences": p.occurrences,
                }
                for p in successful_patterns
            ],
        }

    async def export_patterns(self, output_file: Path):
        """Export patterns to JSON file"""

        patterns_data = []
        for pattern in self.patterns.values():
            patterns_data.append(
                {
                    "id": pattern.id,
                    "type": pattern.type.value,
                    "description": pattern.description,
                    "trigger_conditions": pattern.trigger_conditions,
                    "actions": pattern.actions,
                    "confidence": pattern.confidence,
                    "success_rate": pattern.success_rate,
                    "occurrences": pattern.occurrences,
                    "avg_execution_time": pattern.avg_execution_time,
                    "created_at": pattern.created_at.isoformat(),
                    "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                }
            )

        with open(output_file, "w") as f:
            json.dump(patterns_data, f, indent=2)

        logger.info(f"Exported {len(patterns_data)} patterns to {output_file}")

    async def import_patterns(self, input_file: Path):
        """Import patterns from JSON file"""

        with open(input_file) as f:
            patterns_data = json.load(f)

        imported = 0
        for data in patterns_data:
            pattern = Pattern(
                id=data["id"],
                type=PatternType(data["type"]),
                description=data["description"],
                trigger_conditions=data.get("trigger_conditions", []),
                actions=data.get("actions", []),
                confidence=data.get("confidence", 0.5),
                success_rate=data.get("success_rate", 0.5),
                occurrences=data.get("occurrences", 1),
                avg_execution_time=data.get("avg_execution_time", 0.0),
            )

            if await self.register_pattern(pattern):
                imported += 1

        logger.info(f"Imported {imported} patterns from {input_file}")
