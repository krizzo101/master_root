"""
Recursion management for Claude Code jobs
"""

import hashlib
from typing import Dict, Optional, List
from datetime import datetime

from .config import config
from .models import RecursionContext
from .parallel_logger import logger


class RecursionManager:
    """Manages recursion limits and tracking for Claude Code jobs"""

    def __init__(self):
        self.recursion_contexts: Dict[str, RecursionContext] = {}
        self.depth_counts: Dict[int, int] = {}
        self.root_job_tracking: Dict[str, int] = {}

    def create_recursion_context(
        self,
        job_id: str,
        parent_job_id: Optional[str] = None,
        task: Optional[str] = None,
    ) -> RecursionContext:
        """Create and validate a new recursion context"""
        parent_context = (
            self.recursion_contexts.get(parent_job_id) if parent_job_id else None
        )
        depth = parent_context.depth + 1 if parent_context else 0
        root_job_id = parent_context.root_job_id if parent_context else job_id

        # Check recursion limits
        self.validate_recursion_limits(depth, root_job_id)

        # Build call stack
        call_stack = []
        if parent_context:
            call_stack = parent_context.call_stack.copy()
            if parent_job_id:
                call_stack.append(parent_job_id)

        # Build recursion path
        recursion_path = []
        if parent_context:
            recursion_path = parent_context.recursion_path.copy()
        if task:
            recursion_path.append(self.create_task_signature(task))

        context = RecursionContext(
            job_id=job_id,
            parent_job_id=parent_job_id,
            depth=depth,
            max_depth=config.recursion.max_depth,
            call_stack=call_stack,
            root_job_id=root_job_id,
            recursion_path=recursion_path,
            start_time=datetime.now(),
            is_recursive=depth > 0,
            task=task,
        )

        self.recursion_contexts[job_id] = context
        self.update_depth_counts(depth, 1)
        self.update_root_job_tracking(root_job_id, 1)

        logger.log_recursion(
            job_id,
            "started",
            context,
            {"task": task[:100] if task else None, "parent_job_id": parent_job_id},
        )

        return context

    def validate_recursion_limits(self, depth: int, root_job_id: str) -> None:
        """Validate recursion limits and raise exception if exceeded"""
        # Check depth limit
        if depth >= config.recursion.max_depth:
            raise ValueError(
                f"Recursion depth limit exceeded: {depth}/{config.recursion.max_depth}. "
                f"Job would create infinite loop."
            )

        # Check concurrent jobs at this depth
        current_depth_count = self.depth_counts.get(depth, 0)
        if current_depth_count >= config.recursion.max_concurrent_at_depth:
            raise ValueError(
                f"Too many concurrent jobs at depth {depth}: "
                f"{current_depth_count}/{config.recursion.max_concurrent_at_depth}"
            )

        # Check total jobs for this root
        root_job_count = self.root_job_tracking.get(root_job_id, 0)
        if root_job_count >= config.recursion.max_total_jobs:
            raise ValueError(
                f"Too many total jobs for root {root_job_id}: "
                f"{root_job_count}/{config.recursion.max_total_jobs}"
            )

    def create_task_signature(self, task: str) -> str:
        """Create a unique signature for a task"""
        normalized = task.lower().strip()[:100]
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    def update_depth_counts(self, depth: int, delta: int) -> None:
        """Update job count at a specific depth"""
        current = self.depth_counts.get(depth, 0)
        self.depth_counts[depth] = max(0, current + delta)

    def update_root_job_tracking(self, root_job_id: str, delta: int) -> None:
        """Update job count for a root job"""
        current = self.root_job_tracking.get(root_job_id, 0)
        self.root_job_tracking[root_job_id] = max(0, current + delta)

    def cleanup_job(self, job_id: str) -> None:
        """Clean up recursion context for a completed job"""
        context = self.recursion_contexts.get(job_id)
        if not context:
            return

        # Decrement counters
        self.update_depth_counts(context.depth, -1)
        self.update_root_job_tracking(context.root_job_id, -1)

        del self.recursion_contexts[job_id]

        logger.log(
            "RECURSION",
            job_id,
            "Recursion context cleaned up",
            {
                "depth": context.depth,
                "remaining_at_depth": self.depth_counts.get(context.depth, 0),
                "remaining_for_root": self.root_job_tracking.get(
                    context.root_job_id, 0
                ),
            },
        )

    def get_recursion_stats(self) -> Dict:
        """Get current recursion statistics"""
        return {
            "max_depth": config.recursion.max_depth,
            "depth_counts": dict(self.depth_counts),
            "root_job_counts": dict(self.root_job_tracking),
            "active_contexts": len(self.recursion_contexts),
        }

    def get_active_contexts(self) -> List[RecursionContext]:
        """Get all active recursion contexts"""
        return list(self.recursion_contexts.values())

    def get_timeout_for_depth(self, depth: int) -> int:
        """Calculate timeout based on recursion depth"""
        base_timeout = config.base_timeout
        multiplier = config.recursion.timeout_multiplier**depth
        timeout = int(base_timeout * multiplier)
        return min(timeout, config.max_timeout)
