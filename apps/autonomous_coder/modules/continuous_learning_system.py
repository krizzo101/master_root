"""
Continuous Learning System - Learns from every execution to improve over time
Implements pattern recognition, error recovery, and performance optimization
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns to learn"""
    SUCCESS_PATTERN = "success"
    ERROR_PATTERN = "error"
    OPTIMIZATION_PATTERN = "optimization"
    ARCHITECTURE_PATTERN = "architecture"
    TECHNOLOGY_PATTERN = "technology"


@dataclass
class LearnedPattern:
    """Represents a learned pattern"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    context: Dict[str, Any]
    frequency: int = 1
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    confidence: float = 0.0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    applications: List[str] = field(default_factory=list)
    optimizations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecoveryStrategy:
    """Strategy for recovering from errors"""
    error_pattern: str
    recovery_method: str
    success_rate: float
    avg_recovery_time: float
    preconditions: List[str]
    steps: List[str]
    fallback: Optional[str] = None


class ContinuousLearningSystem:
    """
    Implements continuous learning from execution history
    Improves performance and success rate over time
    """
    
    def __init__(self, storage_path: Path = Path(".learning")):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        
        # Learning databases
        self.pattern_db = self._load_pattern_database()
        self.error_recovery_db = self._load_error_recovery_database()
        self.performance_history = self._load_performance_history()
        self.technology_preferences = self._load_technology_preferences()
        
        # Runtime metrics
        self.current_session_patterns = []
        self.improvement_metrics = {
            "baseline_success_rate": 0.6,
            "current_success_rate": 0.6,
            "patterns_learned": 0,
            "errors_prevented": 0,
            "time_saved": 0.0
        }
    
    async def learn_from_execution(self, 
                                  request: Any,
                                  result: Any,
                                  execution_data: Dict[str, Any]):
        """
        Learn from a completed execution
        """
        # Extract patterns from successful execution
        if result.get("success", False):
            patterns = self._extract_success_patterns(request, result, execution_data)
            for pattern in patterns:
                self._store_pattern(pattern)
        
        # Learn from errors
        if result.get("errors", []):
            error_patterns = self._extract_error_patterns(result["errors"], execution_data)
            for error_pattern in error_patterns:
                self._learn_error_recovery(error_pattern)
        
        # Update performance metrics
        self._update_performance_metrics(execution_data)
        
        # Identify optimization opportunities
        optimizations = self._identify_optimizations(execution_data)
        if optimizations:
            self._store_optimizations(optimizations)
        
        # Persist learning
        await self._persist_learning()
        
        # Calculate improvement
        self._calculate_improvement()
    
    def _extract_success_patterns(self, request, result, execution_data) -> List[LearnedPattern]:
        """Extract patterns from successful execution"""
        patterns = []
        
        # Architecture pattern
        if "architecture" in execution_data:
            pattern = LearnedPattern(
                pattern_id=self._generate_pattern_id("arch", execution_data),
                pattern_type=PatternType.ARCHITECTURE_PATTERN,
                description=f"Architecture for {execution_data.get('project_type', 'unknown')}",
                context={
                    "project_type": execution_data.get("project_type"),
                    "complexity": execution_data.get("complexity"),
                    "architecture": execution_data.get("architecture")
                },
                success_rate=1.0,
                avg_execution_time=execution_data.get("execution_time", 0)
            )
            patterns.append(pattern)
        
        # Technology combination pattern
        if "tech_stack" in execution_data:
            pattern = LearnedPattern(
                pattern_id=self._generate_pattern_id("tech", execution_data),
                pattern_type=PatternType.TECHNOLOGY_PATTERN,
                description=f"Tech stack combination",
                context={
                    "technologies": execution_data.get("tech_stack"),
                    "compatibility": True,
                    "performance": execution_data.get("performance_metrics", {})
                },
                success_rate=1.0
            )
            patterns.append(pattern)
        
        # Agent collaboration pattern
        if "agents_used" in execution_data:
            pattern = LearnedPattern(
                pattern_id=self._generate_pattern_id("agents", execution_data),
                pattern_type=PatternType.OPTIMIZATION_PATTERN,
                description=f"Agent collaboration pattern",
                context={
                    "agents": execution_data.get("agents_used"),
                    "parallel_groups": execution_data.get("parallel_groups", []),
                    "execution_order": execution_data.get("execution_order", [])
                },
                success_rate=1.0,
                avg_execution_time=execution_data.get("execution_time", 0)
            )
            patterns.append(pattern)
        
        return patterns
    
    def _extract_error_patterns(self, errors: List[str], execution_data: Dict) -> List[Dict]:
        """Extract patterns from errors"""
        error_patterns = []
        
        for error in errors:
            pattern = {
                "error_type": self._classify_error(error),
                "error_message": error,
                "context": {
                    "phase": execution_data.get("failed_phase"),
                    "agent": execution_data.get("failed_agent"),
                    "task": execution_data.get("failed_task")
                },
                "timestamp": datetime.now().isoformat()
            }
            error_patterns.append(pattern)
        
        return error_patterns
    
    def _learn_error_recovery(self, error_pattern: Dict):
        """Learn how to recover from errors"""
        error_type = error_pattern["error_type"]
        
        # Check if we have a recovery strategy
        if error_type in self.error_recovery_db:
            strategy = self.error_recovery_db[error_type]
            # Update strategy based on new occurrence
            strategy.frequency += 1
        else:
            # Create new recovery strategy
            strategy = self._create_recovery_strategy(error_pattern)
            self.error_recovery_db[error_type] = strategy
    
    def _create_recovery_strategy(self, error_pattern: Dict) -> ErrorRecoveryStrategy:
        """Create a recovery strategy for an error"""
        error_type = error_pattern["error_type"]
        
        # Define recovery strategies based on error type
        strategies = {
            "timeout": ErrorRecoveryStrategy(
                error_pattern=error_type,
                recovery_method="increase_timeout_and_retry",
                success_rate=0.8,
                avg_recovery_time=30,
                preconditions=["task_can_be_retried", "resources_available"],
                steps=[
                    "Increase timeout by 2x",
                    "Reduce parallel tasks",
                    "Retry with simplified context"
                ],
                fallback="skip_non_essential_task"
            ),
            "dependency": ErrorRecoveryStrategy(
                error_pattern=error_type,
                recovery_method="resolve_dependencies",
                success_rate=0.9,
                avg_recovery_time=20,
                preconditions=["dependencies_identified"],
                steps=[
                    "Identify missing dependencies",
                    "Install or fetch dependencies",
                    "Retry task"
                ],
                fallback="use_alternative_approach"
            ),
            "resource": ErrorRecoveryStrategy(
                error_pattern=error_type,
                recovery_method="optimize_resources",
                success_rate=0.7,
                avg_recovery_time=40,
                preconditions=["resource_limits_known"],
                steps=[
                    "Reduce parallel execution",
                    "Free up resources",
                    "Retry with lower resource requirements"
                ],
                fallback="defer_to_sequential_execution"
            )
        }
        
        return strategies.get(error_type, ErrorRecoveryStrategy(
            error_pattern=error_type,
            recovery_method="generic_retry",
            success_rate=0.5,
            avg_recovery_time=60,
            preconditions=[],
            steps=["Wait and retry", "Simplify task", "Skip if non-essential"],
            fallback="mark_as_known_limitation"
        ))
    
    def apply_learned_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply learned patterns to optimize execution
        """
        optimizations = {
            "suggested_architecture": None,
            "recommended_agents": [],
            "optimal_tech_stack": {},
            "parallel_groups": [],
            "avoid_patterns": [],
            "recovery_strategies": {}
        }
        
        # Find relevant patterns
        relevant_patterns = self._find_relevant_patterns(context)
        
        for pattern in relevant_patterns:
            if pattern.pattern_type == PatternType.ARCHITECTURE_PATTERN:
                if pattern.success_rate > 0.8:
                    optimizations["suggested_architecture"] = pattern.context["architecture"]
            
            elif pattern.pattern_type == PatternType.TECHNOLOGY_PATTERN:
                if pattern.success_rate > 0.85:
                    optimizations["optimal_tech_stack"].update(pattern.context["technologies"])
            
            elif pattern.pattern_type == PatternType.OPTIMIZATION_PATTERN:
                if pattern.confidence > 0.7:
                    optimizations["recommended_agents"] = pattern.context.get("agents", [])
                    optimizations["parallel_groups"] = pattern.context.get("parallel_groups", [])
            
            elif pattern.pattern_type == PatternType.ERROR_PATTERN:
                if pattern.frequency > 3:
                    optimizations["avoid_patterns"].append(pattern.description)
        
        # Add error recovery strategies
        for error_type, strategy in self.error_recovery_db.items():
            if strategy.success_rate > 0.6:
                optimizations["recovery_strategies"][error_type] = {
                    "method": strategy.recovery_method,
                    "steps": strategy.steps,
                    "success_rate": strategy.success_rate
                }
        
        logger.info(f"Applied {len(relevant_patterns)} learned patterns")
        self.improvement_metrics["patterns_applied"] = len(relevant_patterns)
        
        return optimizations
    
    def _find_relevant_patterns(self, context: Dict[str, Any]) -> List[LearnedPattern]:
        """Find patterns relevant to current context"""
        relevant = []
        
        for pattern_id, pattern in self.pattern_db.items():
            similarity = self._calculate_pattern_similarity(pattern.context, context)
            if similarity > 0.7:
                pattern.confidence = similarity
                relevant.append(pattern)
        
        # Sort by confidence and success rate
        relevant.sort(key=lambda p: (p.confidence * p.success_rate), reverse=True)
        
        return relevant[:10]  # Top 10 most relevant
    
    def _calculate_pattern_similarity(self, pattern_context: Dict, current_context: Dict) -> float:
        """Calculate similarity between contexts"""
        score = 0.0
        total_weight = 0.0
        
        # Compare project type (high weight)
        if "project_type" in pattern_context and "project_type" in current_context:
            if pattern_context["project_type"] == current_context["project_type"]:
                score += 0.4
            total_weight += 0.4
        
        # Compare complexity (medium weight)
        if "complexity" in pattern_context and "complexity" in current_context:
            if pattern_context["complexity"] == current_context["complexity"]:
                score += 0.3
            total_weight += 0.3
        
        # Compare requirements overlap (medium weight)
        if "requirements" in pattern_context and "requirements" in current_context:
            pattern_reqs = set(pattern_context["requirements"])
            current_reqs = set(current_context["requirements"])
            if pattern_reqs and current_reqs:
                overlap = len(pattern_reqs.intersection(current_reqs))
                union = len(pattern_reqs.union(current_reqs))
                score += 0.3 * (overlap / union if union > 0 else 0)
            total_weight += 0.3
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def get_error_recovery_strategy(self, error: str) -> Optional[ErrorRecoveryStrategy]:
        """Get recovery strategy for an error"""
        error_type = self._classify_error(error)
        return self.error_recovery_db.get(error_type)
    
    def _classify_error(self, error: str) -> str:
        """Classify error into categories"""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "dependency" in error_lower or "import" in error_lower:
            return "dependency"
        elif "memory" in error_lower or "resource" in error_lower:
            return "resource"
        elif "permission" in error_lower or "access" in error_lower:
            return "permission"
        elif "syntax" in error_lower:
            return "syntax"
        elif "type" in error_lower:
            return "type_error"
        else:
            return "unknown"
    
    def _store_pattern(self, pattern: LearnedPattern):
        """Store a learned pattern"""
        if pattern.pattern_id in self.pattern_db:
            # Update existing pattern
            existing = self.pattern_db[pattern.pattern_id]
            existing.frequency += 1
            existing.last_seen = datetime.now()
            existing.success_rate = (
                (existing.success_rate * (existing.frequency - 1) + pattern.success_rate) 
                / existing.frequency
            )
        else:
            # Store new pattern
            self.pattern_db[pattern.pattern_id] = pattern
            self.improvement_metrics["patterns_learned"] += 1
    
    def _update_performance_metrics(self, execution_data: Dict):
        """Update performance metrics"""
        timestamp = datetime.now()
        
        metrics = {
            "timestamp": timestamp.isoformat(),
            "execution_time": execution_data.get("execution_time", 0),
            "success": execution_data.get("success", False),
            "agents_used": len(execution_data.get("agents_used", [])),
            "parallel_efficiency": execution_data.get("parallel_efficiency", 0),
            "cache_hits": execution_data.get("cache_hits", 0)
        }
        
        self.performance_history.append(metrics)
        
        # Keep only last 1000 executions
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def _identify_optimizations(self, execution_data: Dict) -> Dict[str, Any]:
        """Identify optimization opportunities"""
        optimizations = {}
        
        # Check for slow tasks
        if "task_times" in execution_data:
            slow_tasks = [
                task for task, time in execution_data["task_times"].items()
                if time > execution_data.get("avg_task_time", 0) * 2
            ]
            if slow_tasks:
                optimizations["slow_tasks"] = slow_tasks
        
        # Check for repeated work
        if "cache_misses" in execution_data:
            if execution_data["cache_misses"] > 5:
                optimizations["increase_cache"] = True
        
        # Check for parallel efficiency
        if "parallel_efficiency" in execution_data:
            if execution_data["parallel_efficiency"] < 0.5:
                optimizations["improve_parallelization"] = True
        
        return optimizations
    
    def _store_optimizations(self, optimizations: Dict):
        """Store identified optimizations"""
        pattern = LearnedPattern(
            pattern_id=self._generate_pattern_id("opt", optimizations),
            pattern_type=PatternType.OPTIMIZATION_PATTERN,
            description="Performance optimization opportunity",
            context=optimizations,
            optimizations=optimizations
        )
        self._store_pattern(pattern)
    
    def _calculate_improvement(self):
        """Calculate improvement metrics"""
        if len(self.performance_history) >= 10:
            # Calculate recent success rate
            recent = self.performance_history[-10:]
            recent_success = sum(1 for m in recent if m["success"]) / 10
            
            # Update improvement metrics
            self.improvement_metrics["current_success_rate"] = recent_success
            
            # Calculate improvement
            improvement = (
                (recent_success - self.improvement_metrics["baseline_success_rate"]) 
                / self.improvement_metrics["baseline_success_rate"]
            )
            
            self.improvement_metrics["improvement_percentage"] = improvement * 100
            
            logger.info(f"Learning improvement: {improvement:.2%}")
    
    async def _persist_learning(self):
        """Persist learning to storage"""
        # Save pattern database
        with open(self.storage_path / "patterns.json", "w") as f:
            patterns_dict = {
                pid: asdict(pattern) 
                for pid, pattern in self.pattern_db.items()
            }
            json.dump(patterns_dict, f, indent=2, default=str)
        
        # Save error recovery database
        with open(self.storage_path / "error_recovery.json", "w") as f:
            recovery_dict = {
                error_type: asdict(strategy)
                for error_type, strategy in self.error_recovery_db.items()
            }
            json.dump(recovery_dict, f, indent=2, default=str)
        
        # Save performance history
        with open(self.storage_path / "performance.json", "w") as f:
            json.dump(self.performance_history, f, indent=2)
    
    def _load_pattern_database(self) -> Dict[str, LearnedPattern]:
        """Load pattern database from storage"""
        path = self.storage_path / "patterns.json"
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                return {
                    pid: LearnedPattern(**pattern_data)
                    for pid, pattern_data in data.items()
                }
        return {}
    
    def _load_error_recovery_database(self) -> Dict[str, ErrorRecoveryStrategy]:
        """Load error recovery database"""
        path = self.storage_path / "error_recovery.json"
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                return {
                    error_type: ErrorRecoveryStrategy(**strategy_data)
                    for error_type, strategy_data in data.items()
                }
        return {}
    
    def _load_performance_history(self) -> List[Dict]:
        """Load performance history"""
        path = self.storage_path / "performance.json"
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return []
    
    def _load_technology_preferences(self) -> Dict[str, float]:
        """Load technology preferences based on success"""
        # Calculate from pattern database
        tech_scores = defaultdict(list)
        
        for pattern in self.pattern_db.values():
            if pattern.pattern_type == PatternType.TECHNOLOGY_PATTERN:
                for tech in pattern.context.get("technologies", {}).keys():
                    tech_scores[tech].append(pattern.success_rate)
        
        # Average scores
        preferences = {}
        for tech, scores in tech_scores.items():
            preferences[tech] = sum(scores) / len(scores) if scores else 0.5
        
        return preferences
    
    def _generate_pattern_id(self, prefix: str, data: Dict) -> str:
        """Generate unique pattern ID"""
        import hashlib
        
        # Create deterministic ID from data
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_suffix = hashlib.md5(data_str.encode()).hexdigest()[:8]
        
        return f"{prefix}_{hash_suffix}"
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Get comprehensive learning report"""
        return {
            "patterns_learned": len(self.pattern_db),
            "error_strategies": len(self.error_recovery_db),
            "performance_samples": len(self.performance_history),
            "improvement_metrics": self.improvement_metrics,
            "top_patterns": self._get_top_patterns(),
            "technology_preferences": self.technology_preferences,
            "recent_optimizations": self._get_recent_optimizations()
        }
    
    def _get_top_patterns(self) -> List[Dict]:
        """Get top performing patterns"""
        sorted_patterns = sorted(
            self.pattern_db.values(),
            key=lambda p: p.success_rate * p.frequency,
            reverse=True
        )
        
        return [
            {
                "type": p.pattern_type.value,
                "description": p.description,
                "success_rate": p.success_rate,
                "frequency": p.frequency
            }
            for p in sorted_patterns[:5]
        ]
    
    def _get_recent_optimizations(self) -> List[str]:
        """Get recent optimization recommendations"""
        recent = []
        
        for pattern in self.pattern_db.values():
            if pattern.pattern_type == PatternType.OPTIMIZATION_PATTERN:
                if (datetime.now() - pattern.last_seen).days < 7:
                    for opt_key, opt_value in pattern.optimizations.items():
                        recent.append(f"{opt_key}: {opt_value}")
        
        return recent[:10]