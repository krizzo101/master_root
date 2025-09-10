# Module Loading Fix Specification

## Issue: Enhanced Feature Module Import Failures

**Priority:** CRITICAL  
**Complexity:** HIGH  
**Estimated Time:** 16 hours  
**Risk Level:** HIGH (core functionality missing)

## Problem Statement

The UnifiedOrchestrator attempts to import modules from incorrect paths and references non-existent module files. This causes all enhanced features (quality gates, monitoring, execution planning) to fail.

## Root Cause Analysis

### Import Path Issues:
1. **Wrong Import Path:** `from src.modules.` should be `from src.unified.modules.`
2. **Missing Files:** Only 3 of 5 expected module files exist
3. **Location Mismatch:** Modules exist in `src/unified/modules/` not `src/modules/`

### Missing Modules:
- ❌ `quality_gates_module.py` - NOT FOUND
- ❌ `monitoring_module.py` - NOT FOUND
- ❌ `execution_plan_module.py` - NOT FOUND
- ✅ `collaboration_module.py` - EXISTS (wrong import path)
- ✅ `enhanced_module.py` - EXISTS
- ✅ `orchestrator_module.py` - EXISTS

## Implementation Details

### Phase 1: Create Missing Module Implementations

#### File 1: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/modules/quality_gates_module.py`

**CREATE NEW FILE:**
```python
"""
Quality Gates Module for UnifiedOrchestrator
Provides validation checkpoints during task execution
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from src.unified.modules.base_module import BaseModule, ModuleConfig
from src.models import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class QualityGate:
    """Represents a quality validation checkpoint"""
    name: str
    validator: callable
    required: bool = True
    timeout: float = 30.0
    retry_count: int = 1


class QualityGatesModule(BaseModule):
    """
    Manages quality gates for task validation
    """
    
    def __init__(self, orchestrator, config: ModuleConfig):
        super().__init__(orchestrator, config)
        self.gates: Dict[str, List[QualityGate]] = {}
        self.timeout = config.config.get("timeout", 30)
        self.require_all = config.config.get("require_all", False)
        self._setup_default_gates()
    
    def _setup_default_gates(self):
        """Initialize default quality gates"""
        # Input validation gate
        self.register_gate("pre_execution", QualityGate(
            name="input_validation",
            validator=self._validate_input,
            required=True
        ))
        
        # Output validation gate
        self.register_gate("post_execution", QualityGate(
            name="output_validation",
            validator=self._validate_output,
            required=False
        ))
        
        # Resource check gate
        self.register_gate("pre_execution", QualityGate(
            name="resource_check",
            validator=self._check_resources,
            required=False
        ))
    
    def register_gate(self, phase: str, gate: QualityGate):
        """Register a quality gate for a specific phase"""
        if phase not in self.gates:
            self.gates[phase] = []
        self.gates[phase].append(gate)
        logger.debug(f"Registered gate '{gate.name}' for phase '{phase}'")
    
    async def validate(self, phase: str, task: AgentTask) -> Dict[str, Any]:
        """Run quality gates for a specific phase"""
        results = {
            "phase": phase,
            "task_id": task.task_id,
            "passed": True,
            "gates": [],
            "timestamp": datetime.now().isoformat()
        }
        
        phase_gates = self.gates.get(phase, [])
        if not phase_gates:
            return results
        
        for gate in phase_gates:
            gate_result = {
                "name": gate.name,
                "required": gate.required,
                "passed": False,
                "message": None
            }
            
            try:
                # Run validator with timeout
                import asyncio
                if asyncio.iscoroutinefunction(gate.validator):
                    passed = await asyncio.wait_for(
                        gate.validator(task),
                        timeout=gate.timeout
                    )
                else:
                    passed = gate.validator(task)
                
                gate_result["passed"] = bool(passed)
                
                if not passed and gate.required:
                    results["passed"] = False
                    gate_result["message"] = f"Required gate '{gate.name}' failed"
                    
            except asyncio.TimeoutError:
                gate_result["message"] = f"Gate '{gate.name}' timed out"
                if gate.required:
                    results["passed"] = False
                    
            except Exception as e:
                gate_result["message"] = f"Gate '{gate.name}' error: {str(e)}"
                if gate.required:
                    results["passed"] = False
            
            results["gates"].append(gate_result)
            
            # Early exit if require_all is False and we failed
            if not results["passed"] and not self.require_all:
                break
        
        return results
    
    def _validate_input(self, task: AgentTask) -> bool:
        """Validate task input configuration"""
        # Check required fields
        if not task.task_id:
            return False
        if not task.task_type:
            return False
        if task.config is None:
            return False
        return True
    
    def _validate_output(self, task: AgentTask) -> bool:
        """Validate task output"""
        if task.status == "completed":
            # Check if results exist
            return task.results is not None
        return True
    
    def _check_resources(self, task: AgentTask) -> bool:
        """Check if required resources are available"""
        # Check token availability
        if hasattr(self.orchestrator, 'token_pool'):
            return self.orchestrator.token_pool.available_tokens() > 0
        return True
    
    async def pre_execution_hook(self, task: AgentTask) -> bool:
        """Hook called before task execution"""
        validation = await self.validate("pre_execution", task)
        if not validation["passed"]:
            task.error = f"Quality gate failed: {validation}"
            logger.warning(f"Task {task.task_id} failed pre-execution gates")
            return False
        return True
    
    async def post_execution_hook(self, task: AgentTask) -> bool:
        """Hook called after task execution"""
        validation = await self.validate("post_execution", task)
        if not validation["passed"]:
            logger.warning(f"Task {task.task_id} failed post-execution gates")
            # Don't fail the task, just log warning
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            "total_gates": sum(len(gates) for gates in self.gates.values()),
            "phases": list(self.gates.keys()),
            "require_all": self.require_all,
            "timeout": self.timeout
        }
```

#### File 2: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/modules/monitoring_module.py`

**CREATE NEW FILE:**
```python
"""
Monitoring Module for UnifiedOrchestrator
Provides real-time monitoring and health checks for agent execution
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import psutil
import json

from src.unified.modules.base_module import BaseModule, ModuleConfig
from src.models import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    status_checks: List[Dict] = field(default_factory=list)
    events: List[Dict] = field(default_factory=list)


class MonitoringModule(BaseModule):
    """
    Provides monitoring capabilities for task execution
    """
    
    def __init__(self, orchestrator, config: ModuleConfig):
        super().__init__(orchestrator, config)
        self.check_interval = config.config.get("check_interval", 5.0)
        self.metrics_retention = config.config.get("metrics_retention", 3600)
        self.enable_resource_monitoring = config.config.get("enable_resource_monitoring", True)
        
        self.active_monitors: Dict[str, AgentMetrics] = {}
        self.completed_metrics: List[AgentMetrics] = []
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # System metrics
        self.system_metrics = {
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_duration": 0,
            "system_cpu": 0,
            "system_memory": 0
        }
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system monitoring"""
        asyncio.create_task(self._monitor_system())
    
    async def _monitor_system(self):
        """Monitor system-wide metrics"""
        while True:
            try:
                self.system_metrics["system_cpu"] = psutil.cpu_percent(interval=1)
                self.system_metrics["system_memory"] = psutil.virtual_memory().percent
                self.system_metrics["active_tasks"] = len(self.active_monitors)
                
                # Clean old metrics
                cutoff = datetime.now() - timedelta(seconds=self.metrics_retention)
                self.completed_metrics = [
                    m for m in self.completed_metrics
                    if m.end_time and m.end_time > cutoff
                ]
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def start_monitoring(self, task: AgentTask):
        """Start monitoring an agent task"""
        metrics = AgentMetrics(
            task_id=task.task_id,
            start_time=datetime.now()
        )
        
        self.active_monitors[task.task_id] = metrics
        self.system_metrics["total_tasks"] += 1
        
        # Start background monitoring task
        if self.enable_resource_monitoring:
            monitor_task = asyncio.create_task(
                self._monitor_task(task.task_id)
            )
            self.monitoring_tasks[task.task_id] = monitor_task
        
        logger.debug(f"Started monitoring for task {task.task_id}")
    
    async def _monitor_task(self, task_id: str):
        """Background task to monitor a specific agent"""
        while task_id in self.active_monitors:
            try:
                metrics = self.active_monitors[task_id]
                
                # Collect resource metrics
                metrics.cpu_usage.append(psutil.cpu_percent(interval=0.1))
                metrics.memory_usage.append(psutil.virtual_memory().percent)
                
                # Add status check
                status_check = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": metrics.cpu_usage[-1],
                    "memory": metrics.memory_usage[-1],
                    "duration": (datetime.now() - metrics.start_time).total_seconds()
                }
                metrics.status_checks.append(status_check)
                
                # Check for issues
                if metrics.cpu_usage[-1] > 90:
                    self.log_event(task_id, "warning", "High CPU usage detected")
                if metrics.memory_usage[-1] > 85:
                    self.log_event(task_id, "warning", "High memory usage detected")
                
            except Exception as e:
                logger.error(f"Task monitoring error for {task_id}: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self, task_id: str):
        """Stop monitoring an agent task"""
        if task_id in self.active_monitors:
            metrics = self.active_monitors[task_id]
            metrics.end_time = datetime.now()
            
            # Move to completed
            self.completed_metrics.append(metrics)
            del self.active_monitors[task_id]
            
            # Cancel monitoring task
            if task_id in self.monitoring_tasks:
                self.monitoring_tasks[task_id].cancel()
                del self.monitoring_tasks[task_id]
            
            # Update system metrics
            if metrics.end_time:
                duration = (metrics.end_time - metrics.start_time).total_seconds()
                self.system_metrics["completed_tasks"] += 1
                
                # Update average duration
                total_completed = self.system_metrics["completed_tasks"]
                current_avg = self.system_metrics["avg_duration"]
                self.system_metrics["avg_duration"] = (
                    (current_avg * (total_completed - 1) + duration) / total_completed
                )
            
            logger.debug(f"Stopped monitoring for task {task_id}")
    
    def log_event(self, task_id: str, event_type: str, message: str):
        """Log an event for a task"""
        if task_id in self.active_monitors:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "message": message
            }
            self.active_monitors[task_id].events.append(event)
    
    def get_task_metrics(self, task_id: str) -> Optional[Dict]:
        """Get metrics for a specific task"""
        # Check active monitors
        if task_id in self.active_monitors:
            metrics = self.active_monitors[task_id]
        else:
            # Check completed metrics
            metrics = next(
                (m for m in self.completed_metrics if m.task_id == task_id),
                None
            )
        
        if metrics:
            return {
                "task_id": metrics.task_id,
                "start_time": metrics.start_time.isoformat(),
                "end_time": metrics.end_time.isoformat() if metrics.end_time else None,
                "duration": (
                    (metrics.end_time or datetime.now()) - metrics.start_time
                ).total_seconds(),
                "avg_cpu": sum(metrics.cpu_usage) / len(metrics.cpu_usage) if metrics.cpu_usage else 0,
                "max_cpu": max(metrics.cpu_usage) if metrics.cpu_usage else 0,
                "avg_memory": sum(metrics.memory_usage) / len(metrics.memory_usage) if metrics.memory_usage else 0,
                "max_memory": max(metrics.memory_usage) if metrics.memory_usage else 0,
                "events": metrics.events,
                "status_checks": len(metrics.status_checks)
            }
        
        return None
    
    async def pre_execution_hook(self, task: AgentTask) -> bool:
        """Hook called before task execution"""
        await self.start_monitoring(task)
        return True
    
    async def post_execution_hook(self, task: AgentTask) -> bool:
        """Hook called after task execution"""
        self.stop_monitoring(task.task_id)
        
        # Add metrics to task results
        metrics = self.get_task_metrics(task.task_id)
        if metrics and hasattr(task, 'results'):
            if not task.results:
                task.results = {}
            task.results["monitoring_metrics"] = metrics
        
        # Update failure count
        if task.status == "failed":
            self.system_metrics["failed_tasks"] += 1
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            **self.system_metrics,
            "monitoring_enabled": self.enable_resource_monitoring,
            "check_interval": self.check_interval,
            "active_monitors": list(self.active_monitors.keys()),
            "completed_count": len(self.completed_metrics)
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        health_status = "healthy"
        issues = []
        
        if self.system_metrics["system_cpu"] > 80:
            health_status = "degraded"
            issues.append("High system CPU usage")
        
        if self.system_metrics["system_memory"] > 85:
            health_status = "degraded"
            issues.append("High system memory usage")
        
        if self.system_metrics["failed_tasks"] > self.system_metrics["completed_tasks"] * 0.5:
            health_status = "unhealthy"
            issues.append("High task failure rate")
        
        return {
            "status": health_status,
            "issues": issues,
            "metrics": self.system_metrics,
            "timestamp": datetime.now().isoformat()
        }
```

#### File 3: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/modules/execution_plan_module.py`

**CREATE NEW FILE:**
```python
"""
Execution Plan Module for UnifiedOrchestrator
Provides execution planning and optimization capabilities
"""
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import networkx as nx

from src.unified.modules.base_module import BaseModule, ModuleConfig
from src.models import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class ExecutionPlan:
    """Represents an optimized execution plan"""
    plan_id: str
    created_at: datetime
    tasks: List[AgentTask]
    execution_order: List[List[str]]  # List of parallel batches
    dependency_graph: nx.DiGraph
    estimated_duration: float
    parallelism_factor: float


class ExecutionPlanModule(BaseModule):
    """
    Creates and optimizes execution plans for task batches
    """
    
    def __init__(self, orchestrator, config: ModuleConfig):
        super().__init__(orchestrator, config)
        self.enable_optimization = config.config.get("enable_optimization", True)
        self.max_parallel = config.config.get("max_parallel", 5)
        self.enable_caching = config.config.get("enable_caching", True)
        
        self.current_plan: Optional[ExecutionPlan] = None
        self.plan_cache: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[Dict] = []
    
    def create_plan(self, tasks: List[AgentTask]) -> ExecutionPlan:
        """Create an optimized execution plan for tasks"""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build dependency graph
        graph = self._build_dependency_graph(tasks)
        
        # Calculate execution order
        execution_order = self._calculate_execution_order(graph, tasks)
        
        # Estimate duration
        estimated_duration = self._estimate_duration(execution_order, tasks)
        
        # Calculate parallelism factor
        parallelism_factor = self._calculate_parallelism(execution_order, tasks)
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            created_at=datetime.now(),
            tasks=tasks,
            execution_order=execution_order,
            dependency_graph=graph,
            estimated_duration=estimated_duration,
            parallelism_factor=parallelism_factor
        )
        
        self.current_plan = plan
        
        if self.enable_caching:
            # Cache plan by task signature
            cache_key = self._get_cache_key(tasks)
            self.plan_cache[cache_key] = plan
        
        logger.info(f"Created execution plan {plan_id} with {len(tasks)} tasks")
        logger.info(f"Execution will run in {len(execution_order)} batches")
        logger.info(f"Estimated duration: {estimated_duration:.2f}s")
        logger.info(f"Parallelism factor: {parallelism_factor:.2%}")
        
        return plan
    
    def _build_dependency_graph(self, tasks: List[AgentTask]) -> nx.DiGraph:
        """Build a directed graph of task dependencies"""
        graph = nx.DiGraph()
        
        # Add all tasks as nodes
        for task in tasks:
            graph.add_node(task.task_id, task=task)
        
        # Add dependency edges
        for task in tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id in graph:
                        graph.add_edge(dep_id, task.task_id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")
        
        return graph
    
    def _calculate_execution_order(
        self, 
        graph: nx.DiGraph, 
        tasks: List[AgentTask]
    ) -> List[List[str]]:
        """Calculate optimal execution order with parallelization"""
        if not tasks:
            return []
        
        # Use topological generations for parallel execution
        try:
            generations = list(nx.topological_generations(graph))
            execution_order = [list(gen) for gen in generations]
        except nx.NetworkXError:
            # Fallback to sequential if graph has issues
            execution_order = [[task.task_id] for task in tasks]
        
        # Apply parallelism limits
        limited_order = []
        for batch in execution_order:
            if len(batch) <= self.max_parallel:
                limited_order.append(batch)
            else:
                # Split large batches
                for i in range(0, len(batch), self.max_parallel):
                    limited_order.append(batch[i:i + self.max_parallel])
        
        return limited_order
    
    def _estimate_duration(
        self, 
        execution_order: List[List[str]], 
        tasks: List[AgentTask]
    ) -> float:
        """Estimate total execution duration"""
        task_map = {task.task_id: task for task in tasks}
        total_duration = 0.0
        
        for batch in execution_order:
            # Batch duration is the max duration of tasks in the batch
            batch_duration = 0.0
            for task_id in batch:
                task = task_map.get(task_id)
                if task:
                    # Estimate based on task type
                    estimated = self._estimate_task_duration(task)
                    batch_duration = max(batch_duration, estimated)
            
            total_duration += batch_duration
        
        return total_duration
    
    def _estimate_task_duration(self, task: AgentTask) -> float:
        """Estimate duration for a single task"""
        # Use historical data if available
        historical = self._get_historical_duration(task.task_type)
        if historical:
            return historical
        
        # Default estimates by task type
        estimates = {
            "analysis": 30.0,
            "research": 45.0,
            "monitoring": 20.0,
            "validation": 15.0,
            "test": 10.0
        }
        
        return estimates.get(task.task_type, 25.0)
    
    def _get_historical_duration(self, task_type: str) -> Optional[float]:
        """Get average historical duration for task type"""
        relevant_history = [
            h for h in self.execution_history
            if h.get("task_type") == task_type and h.get("duration")
        ]
        
        if relevant_history:
            durations = [h["duration"] for h in relevant_history]
            return sum(durations) / len(durations)
        
        return None
    
    def _calculate_parallelism(
        self, 
        execution_order: List[List[str]], 
        tasks: List[AgentTask]
    ) -> float:
        """Calculate parallelism factor (0-1)"""
        if not tasks:
            return 0.0
        
        total_tasks = len(tasks)
        total_batches = len(execution_order)
        
        if total_batches == 0:
            return 0.0
        
        # Perfect parallelism would be all tasks in one batch
        # Perfect sequential would be one task per batch
        parallelism = 1.0 - ((total_batches - 1) / max(total_tasks - 1, 1))
        
        return max(0.0, min(1.0, parallelism))
    
    def _get_cache_key(self, tasks: List[AgentTask]) -> str:
        """Generate cache key for task list"""
        # Create signature based on task IDs and dependencies
        signature = []
        for task in sorted(tasks, key=lambda t: t.task_id):
            deps = ",".join(sorted(task.dependencies or []))
            signature.append(f"{task.task_id}:{task.task_type}:{deps}")
        
        return "|".join(signature)
    
    def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Apply optimizations to execution plan"""
        if not self.enable_optimization:
            return plan
        
        # Optimization strategies
        optimized_order = self._optimize_resource_usage(
            plan.execution_order, 
            plan.tasks
        )
        
        # Recalculate metrics
        plan.execution_order = optimized_order
        plan.estimated_duration = self._estimate_duration(optimized_order, plan.tasks)
        plan.parallelism_factor = self._calculate_parallelism(optimized_order, plan.tasks)
        
        logger.info(f"Optimized plan: {plan.parallelism_factor:.2%} parallelism")
        
        return plan
    
    def _optimize_resource_usage(
        self, 
        execution_order: List[List[str]], 
        tasks: List[AgentTask]
    ) -> List[List[str]]:
        """Optimize execution order for resource usage"""
        # Group similar task types together when possible
        task_map = {task.task_id: task for task in tasks}
        
        optimized = []
        for batch in execution_order:
            # Sort batch by task type for better cache locality
            sorted_batch = sorted(
                batch,
                key=lambda tid: task_map[tid].task_type if tid in task_map else ""
            )
            optimized.append(sorted_batch)
        
        return optimized
    
    def record_execution(self, task: AgentTask, duration: float):
        """Record task execution for historical analysis"""
        record = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "status": task.status
        }
        
        self.execution_history.append(record)
        
        # Limit history size
        max_history = 1000
        if len(self.execution_history) > max_history:
            self.execution_history = self.execution_history[-max_history:]
    
    async def pre_batch_hook(self, tasks: List[AgentTask]) -> bool:
        """Hook called before batch execution"""
        # Create execution plan
        plan = self.create_plan(tasks)
        
        if self.enable_optimization:
            plan = self.optimize_plan(plan)
        
        # Store plan for reference
        self.current_plan = plan
        
        return True
    
    async def post_execution_hook(self, task: AgentTask) -> bool:
        """Hook called after task execution"""
        # Record execution time
        if hasattr(task, 'start_time') and hasattr(task, 'end_time'):
            duration = (task.end_time - task.start_time).total_seconds()
            self.record_execution(task, duration)
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        stats = {
            "optimization_enabled": self.enable_optimization,
            "max_parallel": self.max_parallel,
            "cache_enabled": self.enable_caching,
            "cache_size": len(self.plan_cache),
            "history_size": len(self.execution_history)
        }
        
        if self.current_plan:
            stats["current_plan"] = {
                "plan_id": self.current_plan.plan_id,
                "task_count": len(self.current_plan.tasks),
                "batch_count": len(self.current_plan.execution_order),
                "estimated_duration": self.current_plan.estimated_duration,
                "parallelism": self.current_plan.parallelism_factor
            }
        
        return stats
    
    def get_execution_insights(self) -> Dict[str, Any]:
        """Get insights from execution history"""
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        # Calculate statistics by task type
        type_stats = {}
        for record in self.execution_history:
            task_type = record.get("task_type", "unknown")
            if task_type not in type_stats:
                type_stats[task_type] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0
                }
            
            type_stats[task_type]["count"] += 1
            type_stats[task_type]["total_duration"] += record.get("duration", 0)
            if record.get("status") == "completed":
                type_stats[task_type]["success_count"] += 1
        
        # Calculate averages
        for task_type, stats in type_stats.items():
            if stats["count"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["count"]
                stats["success_rate"] = stats["success_count"] / stats["count"]
        
        return {
            "total_executions": len(self.execution_history),
            "type_statistics": type_stats,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }
```

### Phase 2: Fix Import Paths

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/unified_orchestrator.py`

**Lines 273, 298, 319, 343 - FIX ALL IMPORT STATEMENTS:**

**REPLACE:**
```python
from src.modules.quality_gates_module import QualityGatesModule
```
**WITH:**
```python
from src.unified.modules.quality_gates_module import QualityGatesModule
```

**REPLACE:**
```python
from src.modules.monitoring_module import MonitoringModule
```
**WITH:**
```python
from src.unified.modules.monitoring_module import MonitoringModule
```

**REPLACE:**
```python
from src.modules.collaboration_module import CollaborationModule
```
**WITH:**
```python
from src.unified.modules.collaboration_module import CollaborationModule
```

**REPLACE:**
```python
from src.modules.execution_plan_module import ExecutionPlanModule
```
**WITH:**
```python
from src.unified.modules.execution_plan_module import ExecutionPlanModule
```

### Phase 3: Create Base Module (if missing)

#### File: `/home/opsvi/master_root/apps/agent-orchestrator/src/unified/modules/base_module.py`

**CREATE IF NOT EXISTS:**
```python
"""
Base Module for UnifiedOrchestrator modules
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.models import AgentTask


@dataclass
class ModuleConfig:
    """Configuration for a module"""
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class BaseModule(ABC):
    """Base class for all orchestrator modules"""
    
    def __init__(self, orchestrator, config: ModuleConfig):
        self.orchestrator = orchestrator
        self.config = config
        self.enabled = config.enabled
        self.priority = config.priority
    
    async def initialize(self):
        """Initialize the module"""
        pass
    
    async def shutdown(self):
        """Shutdown the module"""
        pass
    
    async def pre_execution_hook(self, task: AgentTask) -> bool:
        """Called before task execution"""
        return True
    
    async def post_execution_hook(self, task: AgentTask) -> bool:
        """Called after task execution"""
        return True
    
    async def pre_batch_hook(self, tasks: list) -> bool:
        """Called before batch execution"""
        return True
    
    async def post_batch_hook(self, results: list) -> bool:
        """Called after batch execution"""
        return True
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        pass
```

## Testing Requirements

### Integration Test:
```python
# test_module_loading.py
import asyncio
from src.unified.unified_orchestrator import UnifiedOrchestrator

async def test_module_loading():
    """Test that all modules load correctly"""
    config = OrchestratorConfig(
        output_dir="test_output",
        enable_quality_gates=True,
        enable_monitoring=True,
        enable_collaboration=True,
        enable_execution_plan=True
    )
    
    orchestrator = UnifiedOrchestrator(config)
    await orchestrator.initialize()
    
    # Verify modules loaded
    assert orchestrator.module_registry.get_module("quality_gates")
    assert orchestrator.module_registry.get_module("monitoring")
    assert orchestrator.module_registry.get_module("execution_plan")
    
    print("✓ All modules loaded successfully")

asyncio.run(test_module_loading())
```

## Validation Criteria

1. All import errors resolved
2. Modules initialize without errors
3. Module hooks are called during execution
4. Quality gates validate tasks
5. Monitoring tracks metrics
6. Execution plans optimize task order

## Implementation Notes for Agent

1. **CREATE ALL THREE MODULE FILES FIRST**
2. **THEN fix import paths**
3. **CREATE base_module.py if it doesn't exist**
4. **TEST each module loads individually**
5. **RUN integration test to verify all modules work together**

## Post-Implementation Checklist

- [ ] All module files created
- [ ] Import paths corrected
- [ ] Base module exists
- [ ] Modules initialize without errors
- [ ] Module hooks execute correctly
- [ ] Quality gates validate tasks
- [ ] Monitoring collects metrics
- [ ] Execution plans generate correctly
- [ ] Integration tests pass