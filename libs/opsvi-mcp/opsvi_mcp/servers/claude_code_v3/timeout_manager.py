"""Dynamic timeout management for Claude Code V3"""

import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import deque
import statistics


@dataclass
class TaskExecutionHistory:
    """Track execution history for learning"""
    task_type: str
    complexity: str
    depth: int
    file_count: int
    actual_time_ms: int
    completed: bool
    timestamp: float = field(default_factory=time.time)


class TimeoutManager:
    """Intelligent timeout management with learning capabilities"""
    
    def __init__(self, config):
        self.config = config
        self.history: deque = deque(maxlen=100)  # Keep last 100 executions
        self.type_statistics: Dict[str, List[int]] = {}
        self.complexity_statistics: Dict[str, List[int]] = {}
        
    def calculate_timeout(
        self, 
        task: str, 
        task_type: str,
        complexity: str,
        depth: int,
        file_count: int = 1,
        parent_timeout: Optional[int] = None
    ) -> int:
        """Calculate dynamic timeout based on multiple factors"""
        
        if not self.config.timeout.enable_adaptive:
            # Use static calculation
            return self.config.timeout.calculate_timeout(complexity, depth, file_count)
        
        # Start with configured calculation
        base_timeout = self.config.timeout.calculate_timeout(complexity, depth, file_count)
        
        # Apply learning if enabled and data available
        if self.config.timeout.learning_enabled:
            learned_timeout = self._calculate_from_history(
                task_type, complexity, depth, file_count
            )
            if learned_timeout:
                # Blend base and learned timeouts
                base_timeout = int(base_timeout * 0.3 + learned_timeout * 0.7)
        
        # Apply parent timeout constraint if exists
        if parent_timeout:
            # Child timeout should not exceed parent's remaining time
            remaining_parent = parent_timeout - int(time.time() * 1000)
            if remaining_parent > 0:
                base_timeout = min(base_timeout, int(remaining_parent * 0.8))
        
        # Apply min/max bounds
        min_timeout = 60000  # 1 minute minimum
        max_timeout = self.config.timeout.max_timeout
        
        return max(min_timeout, min(base_timeout, max_timeout))
    
    def _calculate_from_history(
        self,
        task_type: str,
        complexity: str,
        depth: int,
        file_count: int
    ) -> Optional[int]:
        """Calculate timeout based on historical data"""
        
        # Find similar tasks in history
        similar_tasks = [
            h for h in self.history
            if h.task_type == task_type 
            and h.complexity == complexity
            and abs(h.depth - depth) <= 1
            and abs(h.file_count - file_count) <= 2
        ]
        
        if len(similar_tasks) < 3:
            # Not enough data for reliable prediction
            return None
        
        # Calculate statistics from successful completions
        successful_times = [
            t.actual_time_ms for t in similar_tasks 
            if t.completed
        ]
        
        if not successful_times:
            # No successful completions, use failed attempts with buffer
            failed_times = [t.actual_time_ms for t in similar_tasks]
            if failed_times:
                # Add 50% buffer to max failed time
                return int(max(failed_times) * 1.5)
            return None
        
        # Use 90th percentile of successful times with small buffer
        percentile_90 = statistics.quantiles(successful_times, n=10)[8] if len(successful_times) > 10 else max(successful_times)
        return int(percentile_90 * 1.2)  # 20% buffer
    
    def record_execution(
        self,
        task_type: str,
        complexity: str,
        depth: int,
        file_count: int,
        actual_time_ms: int,
        completed: bool
    ):
        """Record execution for learning"""
        
        history_entry = TaskExecutionHistory(
            task_type=task_type,
            complexity=complexity,
            depth=depth,
            file_count=file_count,
            actual_time_ms=actual_time_ms,
            completed=completed
        )
        
        self.history.append(history_entry)
        
        # Update statistics
        if task_type not in self.type_statistics:
            self.type_statistics[task_type] = []
        self.type_statistics[task_type].append(actual_time_ms)
        
        if complexity not in self.complexity_statistics:
            self.complexity_statistics[complexity] = []
        self.complexity_statistics[complexity].append(actual_time_ms)
    
    def get_timeout_with_decay(
        self,
        initial_timeout: int,
        elapsed_ms: int,
        checkpoint_progress: float = 0.0
    ) -> int:
        """Calculate remaining timeout with decay based on progress"""
        
        remaining = initial_timeout - elapsed_ms
        
        if remaining <= 0:
            return 0
        
        # If good progress, extend timeout
        if checkpoint_progress > 0.7:
            # 70% complete, extend by 30%
            remaining = int(remaining * 1.3)
        elif checkpoint_progress > 0.5:
            # 50% complete, extend by 15%
            remaining = int(remaining * 1.15)
        
        return remaining
    
    def should_extend_timeout(
        self,
        job_id: str,
        elapsed_ms: int,
        progress: float,
        recent_activity: bool
    ) -> Tuple[bool, int]:
        """Determine if timeout should be extended"""
        
        # Don't extend if no recent activity
        if not recent_activity:
            return False, 0
        
        # Good progress threshold
        if progress > 0.6 and elapsed_ms > 180000:  # 3+ minutes and 60%+ complete
            # Grant extension proportional to progress
            extension = int(60000 * (1 + progress))  # 1-2 minutes based on progress
            return True, extension
        
        return False, 0
    
    def calculate_retry_timeout(
        self,
        original_timeout: int,
        failure_reason: str,
        attempt_number: int
    ) -> int:
        """Calculate timeout for retry attempt"""
        
        multipliers = {
            'timeout': 2.0,      # Double for timeout failures
            'resource': 1.5,     # 50% increase for resource issues
            'error': 1.2,        # 20% increase for errors
            'unknown': 1.5       # 50% increase for unknown
        }
        
        multiplier = multipliers.get(failure_reason, 1.5)
        
        # Exponential backoff for multiple attempts
        attempt_multiplier = 1.0 + (attempt_number * 0.5)
        
        new_timeout = int(original_timeout * multiplier * attempt_multiplier)
        
        # Cap at max timeout
        return min(new_timeout, self.config.timeout.max_timeout)
    
    def get_statistics(self) -> Dict:
        """Get timeout statistics for monitoring"""
        
        if not self.history:
            return {
                'total_executions': 0,
                'completion_rate': 0.0,
                'avg_completion_time': 0,
                'timeout_accuracy': 0.0
            }
        
        total = len(self.history)
        completed = sum(1 for h in self.history if h.completed)
        completion_rate = completed / total if total > 0 else 0
        
        completion_times = [h.actual_time_ms for h in self.history if h.completed]
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0
        
        # Calculate timeout accuracy (how often timeout was sufficient)
        accurate_timeouts = sum(
            1 for h in self.history 
            if h.completed or h.actual_time_ms < self.config.timeout.max_timeout * 0.9
        )
        timeout_accuracy = accurate_timeouts / total if total > 0 else 0
        
        return {
            'total_executions': total,
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'timeout_accuracy': timeout_accuracy,
            'type_stats': {
                k: {
                    'count': len(v),
                    'avg_time': statistics.mean(v) if v else 0
                }
                for k, v in self.type_statistics.items()
            },
            'complexity_stats': {
                k: {
                    'count': len(v),
                    'avg_time': statistics.mean(v) if v else 0
                }
                for k, v in self.complexity_statistics.items()
            }
        }