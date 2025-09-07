#!/usr/bin/env python3
"""
Enhanced DependencyManager with comprehensive debug logging

This module provides a DependencyManager implementation with detailed logging
of all dependency operations, state changes, and decision logic.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Set

try:
    from .debug_logger import DebugLogger, TimedOperation
except ImportError:
    from debug_logger import DebugLogger, TimedOperation


class EnhancedDependencyManager:
    """
    Enhanced DependencyManager with comprehensive debug logging.
    
    Logs every dependency check, state transition, and decision point
    to enable detailed analysis of task dependency resolution.
    """
    
    def __init__(self, output_dir: Path = None):
        # Setup debug logging
        if output_dir:
            self.debug_logger = DebugLogger("DependencyManager", output_dir)
        else:
            # Fallback to basic logging if no output_dir
            import logging
            self.debug_logger = logging.getLogger("DependencyManager")
        
        # Initialize state tracking
        self.completed: set = set()
        self.running: set = set()
        self.failed: set = set()
        self.lock = asyncio.Lock()
        
        # Enhanced tracking
        self.dependency_checks = 0
        self.state_transitions = []
        self.deadlock_checks = 0
        self.dependency_graph = {}  # Track task -> dependencies mapping
        
        # Log initialization
        self.debug_logger.log_values("DependencyManager.__init__",
            completed_tasks=list(self.completed),
            running_tasks=list(self.running),
            failed_tasks=list(self.failed),
            dependency_checks=self.dependency_checks
        )
        
        self.debug_logger.info("DependencyManager initialized")
    
    def _record_state_transition(self, task_id: str, old_state: str, new_state: str, **context):
        """Record state transition for analysis"""
        transition = {
            "timestamp": time.time(),
            "task_id": task_id,
            "old_state": old_state,
            "new_state": new_state,
            **context
        }
        self.state_transitions.append(transition)
        
        self.debug_logger.log_values("DependencyManager.state_transition",
            task_id=task_id,
            old_state=old_state,
            new_state=new_state,
            **context
        )
        
        self.debug_logger.debug(f"State transition: {task_id} {old_state} -> {new_state}",
                               **context)
    
    def _get_current_state(self, task_id: str) -> str:
        """Get current state of a task"""
        if task_id in self.completed:
            return "completed"
        elif task_id in self.running:
            return "running"
        elif task_id in self.failed:
            return "failed"
        else:
            return "pending"
    
    def _analyze_dependency_chain(self, task_id: str, dependencies: List[str]) -> Dict:
        """Analyze dependency chain for potential issues"""
        analysis = {
            "task_id": task_id,
            "total_dependencies": len(dependencies),
            "met_dependencies": [],
            "unmet_dependencies": [],
            "failed_dependencies": [],
            "circular_dependencies": [],
            "dependency_depth": 0
        }
        
        for dep in dependencies:
            if dep in self.completed:
                analysis["met_dependencies"].append(dep)
            elif dep in self.failed:
                analysis["failed_dependencies"].append(dep)
            else:
                analysis["unmet_dependencies"].append(dep)
                
                # Check for circular dependencies
                if dep in self.dependency_graph:
                    dep_deps = self.dependency_graph[dep]
                    if task_id in dep_deps:
                        analysis["circular_dependencies"].append(dep)
        
        # Calculate dependency depth (simplified)
        if dependencies:
            max_depth = 1
            for dep in dependencies:
                if dep in self.dependency_graph:
                    dep_depth = len(self.dependency_graph[dep])
                    max_depth = max(max_depth, dep_depth + 1)
            analysis["dependency_depth"] = max_depth
        
        return analysis
    
    async def can_run(self, task) -> bool:
        """Check if task dependencies are satisfied with comprehensive logging"""
        check_start = time.time()
        self.dependency_checks += 1
        
        # Extract task info
        task_id = task.task_id
        dependencies = getattr(task, 'dependencies', [])
        task_type = getattr(task, 'task_type', 'unknown')
        
        # Update dependency graph
        self.dependency_graph[task_id] = dependencies
        
        with TimedOperation(self.debug_logger, f"can_run_check_{task_id}",
                           task_id=task_id, dependency_count=len(dependencies)):
            
            # Log pre-check state
            self.debug_logger.log_values("DependencyManager.can_run.pre_check",
                task_id=task_id,
                task_type=task_type,
                dependencies=dependencies,
                dependency_count=len(dependencies),
                total_dependency_checks=self.dependency_checks,
                current_completed=list(self.completed),
                current_running=list(self.running),
                current_failed=list(self.failed)
            )
            
            async with self.lock:
                lock_acquired_time = time.time()
                
                # Analyze dependency chain
                dependency_analysis = self._analyze_dependency_chain(task_id, dependencies)
                
                # Log dependency analysis
                self.debug_logger.log_values("DependencyManager.can_run.dependency_analysis",
                    **dependency_analysis
                )
                
                # Check if already running or completed
                current_state = self._get_current_state(task_id)
                if task_id in self.running or task_id in self.completed:
                    reason = "already_running_or_completed"
                    
                    self.debug_logger.log_values("DependencyManager.can_run.blocked",
                        task_id=task_id,
                        reason=reason,
                        current_state=current_state,
                        in_running=task_id in self.running,
                        in_completed=task_id in self.completed
                    )
                    
                    self.debug_logger.debug(f"Task {task_id} cannot run: {reason}",
                                           current_state=current_state)
                    
                    return False
                
                # Check dependencies
                unmet_deps = []
                failed_deps = []
                
                for dep in dependencies:
                    if dep in self.failed:
                        failed_deps.append(dep)
                    elif dep not in self.completed:
                        unmet_deps.append(dep)
                
                can_run = len(unmet_deps) == 0 and len(failed_deps) == 0
                
                # Detailed dependency status
                dependency_status = {
                    dep: {
                        "status": self._get_current_state(dep),
                        "in_completed": dep in self.completed,
                        "in_running": dep in self.running,
                        "in_failed": dep in self.failed
                    } for dep in dependencies
                }
                
                # Log decision result
                self.debug_logger.log_values("DependencyManager.can_run.decision",
                    task_id=task_id,
                    can_run=can_run,
                    unmet_dependencies=unmet_deps,
                    failed_dependencies=failed_deps,
                    met_dependencies=dependency_analysis["met_dependencies"],
                    dependency_status=dependency_status,
                    all_completed=list(self.completed),
                    all_running=list(self.running),
                    all_failed=list(self.failed),
                    total_tasks_tracked=len(self.completed | self.running | self.failed)
                )
                
                # Check for potential deadlocks if cannot run
                if not can_run and not unmet_deps and not failed_deps:
                    # This shouldn't happen - log as potential issue
                    self.debug_logger.warning("Inconsistent dependency state detected",
                                             task_id=task_id,
                                             dependencies=dependencies,
                                             unmet_deps=unmet_deps,
                                             failed_deps=failed_deps)
                
                # Performance logging
                lock_duration = time.time() - lock_acquired_time
                total_duration = time.time() - check_start
                
                self.debug_logger.log_performance("DependencyManager.can_run", total_duration,
                    task_id=task_id,
                    dependency_count=len(dependencies),
                    unmet_count=len(unmet_deps),
                    failed_count=len(failed_deps),
                    lock_duration=lock_duration,
                    decision=can_run
                )
                
                if can_run:
                    self.debug_logger.debug(f"Task {task_id} CAN RUN - all dependencies met",
                                           dependencies_met=dependency_analysis["met_dependencies"])
                else:
                    blocking_reason = []
                    if unmet_deps:
                        blocking_reason.append(f"unmet_deps: {unmet_deps}")
                    if failed_deps:
                        blocking_reason.append(f"failed_deps: {failed_deps}")
                    
                    self.debug_logger.debug(f"Task {task_id} CANNOT RUN - {'; '.join(blocking_reason) or 'unknown reason'}")
                
                return can_run
    
    async def mark_running(self, task_id: str):
        """Mark task as running with comprehensive logging"""
        with TimedOperation(self.debug_logger, f"mark_running_{task_id}", task_id=task_id):
            
            async with self.lock:
                old_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_running.pre",
                    task_id=task_id,
                    old_state=old_state,
                    current_running=list(self.running),
                    current_completed=list(self.completed),
                    current_failed=list(self.failed),
                    total_running_before=len(self.running)
                )
                
                self.running.add(task_id)
                
                new_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_running.post",
                    task_id=task_id,
                    new_state=new_state,
                    new_running=list(self.running),
                    running_count=len(self.running),
                    total_running_after=len(self.running)
                )
                
                self._record_state_transition(task_id, old_state, new_state,
                                            action="mark_running",
                                            running_count=len(self.running))
                
                self.debug_logger.info(f"Task {task_id} marked as RUNNING",
                                      total_running=len(self.running))
    
    async def mark_completed(self, task_id: str):
        """Mark task as completed with comprehensive logging"""
        with TimedOperation(self.debug_logger, f"mark_completed_{task_id}", task_id=task_id):
            
            async with self.lock:
                old_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_completed.pre",
                    task_id=task_id,
                    old_state=old_state,
                    current_running=list(self.running),
                    current_completed=list(self.completed),
                    was_running=task_id in self.running,
                    total_completed_before=len(self.completed)
                )
                
                # Remove from running, add to completed
                self.running.discard(task_id)
                self.completed.add(task_id)
                
                new_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_completed.post",
                    task_id=task_id,
                    new_state=new_state,
                    new_running=list(self.running),
                    new_completed=list(self.completed),
                    completed_count=len(self.completed),
                    running_count=len(self.running)
                )
                
                self._record_state_transition(task_id, old_state, new_state,
                                            action="mark_completed",
                                            completed_count=len(self.completed),
                                            running_count=len(self.running))
                
                self.debug_logger.info(f"Task {task_id} marked as COMPLETED",
                                      total_completed=len(self.completed),
                                      total_running=len(self.running))
                
                # Check if this completion unblocks other tasks
                await self._check_newly_unblocked_tasks(task_id)
    
    async def mark_failed(self, task_id: str, failure_reason: str = None):
        """Mark task as failed with comprehensive logging"""
        with TimedOperation(self.debug_logger, f"mark_failed_{task_id}", 
                           task_id=task_id, failure_reason=failure_reason):
            
            async with self.lock:
                old_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_failed.pre",
                    task_id=task_id,
                    old_state=old_state,
                    failure_reason=failure_reason,
                    current_running=list(self.running),
                    current_failed=list(self.failed),
                    was_running=task_id in self.running,
                    total_failed_before=len(self.failed)
                )
                
                # Remove from running, add to failed
                self.running.discard(task_id)
                self.failed.add(task_id)
                
                new_state = self._get_current_state(task_id)
                
                self.debug_logger.log_values("DependencyManager.mark_failed.post",
                    task_id=task_id,
                    new_state=new_state,
                    failure_reason=failure_reason,
                    new_running=list(self.running),
                    new_failed=list(self.failed),
                    failed_count=len(self.failed),
                    running_count=len(self.running)
                )
                
                self._record_state_transition(task_id, old_state, new_state,
                                            action="mark_failed",
                                            failure_reason=failure_reason,
                                            failed_count=len(self.failed),
                                            running_count=len(self.running))
                
                self.debug_logger.warning(f"Task {task_id} marked as FAILED",
                                         failure_reason=failure_reason,
                                         total_failed=len(self.failed),
                                         total_running=len(self.running))
                
                # Check impact of this failure on dependent tasks
                await self._analyze_failure_impact(task_id)
    
    async def _check_newly_unblocked_tasks(self, completed_task_id: str):
        """Check which tasks might now be unblocked by this completion"""
        potentially_unblocked = []
        
        for task_id, dependencies in self.dependency_graph.items():
            if (completed_task_id in dependencies and 
                task_id not in self.completed and 
                task_id not in self.running and 
                task_id not in self.failed):
                potentially_unblocked.append(task_id)
        
        if potentially_unblocked:
            self.debug_logger.log_values("DependencyManager.potentially_unblocked_tasks",
                completed_task=completed_task_id,
                potentially_unblocked=potentially_unblocked
            )
            
            self.debug_logger.debug(f"Task {completed_task_id} completion may unblock tasks",
                                   potentially_unblocked=potentially_unblocked)
    
    async def _analyze_failure_impact(self, failed_task_id: str):
        """Analyze the impact of a task failure on dependent tasks"""
        impacted_tasks = []
        
        for task_id, dependencies in self.dependency_graph.items():
            if (failed_task_id in dependencies and 
                task_id not in self.completed and 
                task_id not in self.failed):
                impacted_tasks.append(task_id)
        
        if impacted_tasks:
            self.debug_logger.log_values("DependencyManager.failure_impact_analysis",
                failed_task=failed_task_id,
                impacted_tasks=impacted_tasks,
                impact_count=len(impacted_tasks)
            )
            
            self.debug_logger.warning(f"Task {failed_task_id} failure will block dependent tasks",
                                     impacted_tasks=impacted_tasks,
                                     impact_count=len(impacted_tasks))
    
    def detect_deadlocks(self) -> Dict:
        """Detect potential deadlock situations"""
        self.deadlock_checks += 1
        
        deadlock_analysis = {
            "check_number": self.deadlock_checks,
            "timestamp": time.time(),
            "pending_tasks": [],
            "potential_deadlocks": [],
            "circular_dependencies": [],
            "orphaned_tasks": []
        }
        
        # Find tasks that are not completed, running, or failed
        for task_id, dependencies in self.dependency_graph.items():
            if (task_id not in self.completed and 
                task_id not in self.running and 
                task_id not in self.failed):
                
                deadlock_analysis["pending_tasks"].append(task_id)
                
                # Check if all dependencies are also pending (potential deadlock)
                unmet_deps = [dep for dep in dependencies if dep not in self.completed]
                failed_deps = [dep for dep in dependencies if dep in self.failed]
                
                if unmet_deps and not failed_deps:
                    # All unmet deps are also pending - potential deadlock
                    pending_deps = [dep for dep in unmet_deps if dep in self.dependency_graph and
                                   dep not in self.completed and dep not in self.running and dep not in self.failed]
                    
                    if pending_deps:
                        deadlock_analysis["potential_deadlocks"].append({
                            "task_id": task_id,
                            "pending_dependencies": pending_deps
                        })
                
                # Check for circular dependencies
                for dep in dependencies:
                    if dep in self.dependency_graph:
                        dep_deps = self.dependency_graph[dep]
                        if task_id in dep_deps:
                            deadlock_analysis["circular_dependencies"].append({
                                "task_a": task_id,
                                "task_b": dep
                            })
        
        self.debug_logger.log_values("DependencyManager.deadlock_analysis", **deadlock_analysis)
        
        if deadlock_analysis["potential_deadlocks"] or deadlock_analysis["circular_dependencies"]:
            self.debug_logger.warning("Potential deadlock situation detected",
                                     deadlock_count=len(deadlock_analysis["potential_deadlocks"]),
                                     circular_count=len(deadlock_analysis["circular_dependencies"]))
        
        return deadlock_analysis
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics about dependency management"""
        stats = {
            "total_completed": len(self.completed),
            "total_running": len(self.running),
            "total_failed": len(self.failed),
            "total_tracked": len(self.completed | self.running | self.failed),
            "dependency_checks": self.dependency_checks,
            "state_transitions": len(self.state_transitions),
            "deadlock_checks": self.deadlock_checks,
            "tasks_in_graph": len(self.dependency_graph),
            "average_dependencies_per_task": 0,
            "max_dependencies": 0,
            "tasks_with_no_dependencies": 0
        }
        
        if self.dependency_graph:
            dep_counts = [len(deps) for deps in self.dependency_graph.values()]
            stats["average_dependencies_per_task"] = sum(dep_counts) / len(dep_counts)
            stats["max_dependencies"] = max(dep_counts)
            stats["tasks_with_no_dependencies"] = sum(1 for count in dep_counts if count == 0)
        
        self.debug_logger.log_values("DependencyManager.stats", **stats)
        
        return stats
    
    def log_summary(self):
        """Log comprehensive summary of dependency manager state"""
        stats = self.get_stats()
        
        self.debug_logger.info("Dependency Manager Summary", **stats)
        
        # Log current state
        self.debug_logger.log_values("DependencyManager.current_state",
            completed_tasks=list(self.completed),
            running_tasks=list(self.running),
            failed_tasks=list(self.failed),
            dependency_graph=dict(self.dependency_graph)
        )
        
        # Log recent state transitions
        if self.state_transitions:
            recent_transitions = self.state_transitions[-10:]  # Last 10
            self.debug_logger.log_values("DependencyManager.recent_transitions",
                                        recent_transitions=recent_transitions)
        
        # Perform deadlock detection
        deadlock_analysis = self.detect_deadlocks()
        
        return stats