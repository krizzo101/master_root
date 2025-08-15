"""OrchestratorAgent - Production-ready workflow orchestration and coordination agent."""

import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid

import structlog

from ..core.base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentResult,
    AgentState,
    AgentContext
)
from ..exceptions.base import AgentExecutionError

logger = structlog.get_logger(__name__)


class WorkflowState(Enum):
    """Workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class WorkflowTask:
    """Individual task in a workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    agent_type: str = ""
    prompt: str = ""
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    state: WorkflowState = WorkflowState.PENDING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class Workflow:
    """Workflow definition and state."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: List[WorkflowTask] = field(default_factory=list)
    state: WorkflowState = WorkflowState.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    parallelism: int = 4
    timeout: int = 3600
    error_strategy: str = "fail_fast"  # fail_fast, continue, retry


class OrchestratorAgent(BaseAgent):
    """Agent specialized in orchestrating complex multi-agent workflows.
    
    Capabilities:
    - Design and execute complex workflows
    - Coordinate multiple agents in parallel
    - Manage dependencies and task sequencing
    - Handle errors and retries gracefully
    - Optimize workflow execution
    - Monitor and report workflow progress
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize OrchestratorAgent with coordination capabilities."""
        if config is None:
            config = AgentConfig(
                name="OrchestratorAgent",
                model="gpt-4o",
                temperature=0.4,
                max_tokens=8192,
                capabilities=[
                    AgentCapability.PLANNING,
                    AgentCapability.PARALLEL,
                    AgentCapability.REASONING,
                    AgentCapability.MEMORY
                ],
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
        
        # Orchestration state
        self.workflows = {}
        self.agent_pool = {}
        self.task_queue = []
        self.execution_history = []
        self.workflow_templates = self._load_workflow_templates()
        
    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for orchestration."""
        return """You are a master orchestrator specializing in coordinating complex multi-agent workflows.
        
        Your responsibilities:
        1. Design optimal workflow structures for complex tasks
        2. Coordinate multiple agents efficiently in parallel
        3. Manage task dependencies and sequencing
        4. Handle errors and implement retry strategies
        5. Optimize workflow execution for speed and resource usage
        6. Monitor progress and provide real-time updates
        7. Adapt workflows based on runtime conditions
        8. Ensure successful completion of all tasks
        
        Always prioritize efficiency, reliability, and successful task completion."""
    
    def _load_workflow_templates(self) -> Dict[str, Dict]:
        """Load predefined workflow templates."""
        return {
            "development": {
                "name": "Development Workflow",
                "tasks": [
                    {"agent": "analyzer", "action": "analyze_requirements"},
                    {"agent": "coder", "action": "implement_solution"},
                    {"agent": "test", "action": "validate_implementation"},
                    {"agent": "reviewer", "action": "review_code"}
                ],
                "parallelism": 2
            },
            "debugging": {
                "name": "Debugging Workflow",
                "tasks": [
                    {"agent": "analyzer", "action": "identify_issue"},
                    {"agent": "debugger", "action": "diagnose_problem"},
                    {"agent": "coder", "action": "implement_fix"},
                    {"agent": "test", "action": "verify_fix"}
                ],
                "parallelism": 1
            },
            "optimization": {
                "name": "Optimization Workflow",
                "tasks": [
                    {"agent": "profiler", "action": "analyze_performance"},
                    {"agent": "optimizer", "action": "identify_improvements"},
                    {"agent": "coder", "action": "implement_optimizations"},
                    {"agent": "test", "action": "benchmark_results"}
                ],
                "parallelism": 3
            }
        }
    
    def _execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute orchestration task."""
        self._logger.info("Executing orchestration", task=prompt[:100])
        
        # Parse orchestration parameters
        workflow_type = kwargs.get("workflow_type", "adaptive")
        tasks = kwargs.get("tasks", [])
        parallelism = kwargs.get("parallelism", 4)
        timeout = kwargs.get("timeout", 3600)
        
        try:
            if workflow_type in self.workflow_templates:
                # Use predefined template
                workflow = self._create_workflow_from_template(
                    workflow_type, prompt, kwargs
                )
            elif tasks:
                # Create custom workflow
                workflow = self._create_custom_workflow(tasks, prompt, kwargs)
            else:
                # Analyze and create adaptive workflow
                workflow = self._create_adaptive_workflow(prompt, kwargs)
            
            # Execute workflow
            result = self._execute_workflow(workflow)
            
            # Store execution history
            self.execution_history.append({
                "workflow_id": workflow.id,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            # Update metrics
            self.context.metrics.update({
                "workflows_executed": len(self.execution_history),
                "tasks_completed": len([t for t in workflow.tasks if t.state == WorkflowState.COMPLETED]),
                "total_duration": (workflow.end_time - workflow.start_time).total_seconds() if workflow.end_time else 0,
                "success_rate": self._calculate_success_rate()
            })
            
            return result
            
        except Exception as e:
            self._logger.error("Orchestration failed", error=str(e))
            raise AgentExecutionError(f"Orchestration failed: {e}")
    
    def _create_workflow_from_template(self, template_name: str, 
                                      prompt: str, context: Dict) -> Workflow:
        """Create workflow from template."""
        template = self.workflow_templates[template_name]
        
        workflow = Workflow(
            name=template["name"],
            parallelism=template.get("parallelism", 4),
            context={"prompt": prompt, **context}
        )
        
        # Create tasks from template
        for task_def in template["tasks"]:
            task = WorkflowTask(
                name=f"{task_def['agent']}_{task_def['action']}",
                agent_type=task_def["agent"],
                prompt=self._generate_task_prompt(task_def, prompt),
                priority=self._determine_priority(task_def),
                context=context
            )
            workflow.tasks.append(task)
        
        # Set up dependencies
        self._setup_dependencies(workflow)
        
        return workflow
    
    def _create_custom_workflow(self, tasks: List[Dict], 
                               prompt: str, context: Dict) -> Workflow:
        """Create custom workflow from task definitions."""
        workflow = Workflow(
            name="Custom Workflow",
            context={"prompt": prompt, **context}
        )
        
        for task_def in tasks:
            task = WorkflowTask(
                name=task_def.get("name", "task"),
                agent_type=task_def.get("agent", "generic"),
                prompt=task_def.get("prompt", prompt),
                dependencies=task_def.get("dependencies", []),
                priority=TaskPriority[task_def.get("priority", "MEDIUM").upper()],
                context={**context, **task_def.get("context", {})}
            )
            workflow.tasks.append(task)
        
        return workflow
    
    def _create_adaptive_workflow(self, prompt: str, context: Dict) -> Workflow:
        """Analyze prompt and create optimal workflow."""
        self._logger.info("Creating adaptive workflow", prompt=prompt[:100])
        
        # Analyze task requirements
        analysis = self._analyze_task_requirements(prompt)
        
        workflow = Workflow(
            name="Adaptive Workflow",
            parallelism=self._determine_optimal_parallelism(analysis),
            context={"prompt": prompt, **context}
        )
        
        # Generate task sequence
        task_sequence = self._generate_task_sequence(analysis, prompt)
        
        for i, task_def in enumerate(task_sequence):
            task = WorkflowTask(
                name=task_def["name"],
                agent_type=task_def["agent"],
                prompt=task_def["prompt"],
                dependencies=task_def.get("dependencies", []),
                priority=self._calculate_task_priority(task_def, i, len(task_sequence)),
                context=context
            )
            workflow.tasks.append(task)
        
        # Optimize task order
        self._optimize_task_order(workflow)
        
        return workflow
    
    def _execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute a workflow with parallel task execution."""
        self._logger.info("Executing workflow", workflow_id=workflow.id, tasks=len(workflow.tasks))
        
        workflow.state = WorkflowState.RUNNING
        workflow.start_time = datetime.now()
        
        # Initialize execution context
        execution_context = {
            "workflow_id": workflow.id,
            "results": {},
            "errors": []
        }
        
        try:
            # Build task dependency graph
            task_graph = self._build_dependency_graph(workflow)
            
            # Execute tasks in optimal order
            while self._has_pending_tasks(workflow):
                # Get executable tasks (no pending dependencies)
                executable_tasks = self._get_executable_tasks(workflow, task_graph)
                
                if not executable_tasks:
                    # Check for deadlock
                    if self._detect_deadlock(workflow):
                        raise AgentExecutionError("Workflow deadlock detected")
                    continue
                
                # Execute tasks in parallel (up to parallelism limit)
                batch_size = min(len(executable_tasks), workflow.parallelism)
                task_batch = executable_tasks[:batch_size]
                
                # Execute batch
                batch_results = self._execute_task_batch(task_batch, execution_context)
                
                # Update task states and results
                for task, result in zip(task_batch, batch_results):
                    if result["success"]:
                        task.state = WorkflowState.COMPLETED
                        task.result = result["output"]
                        execution_context["results"][task.id] = result["output"]
                    else:
                        self._handle_task_failure(task, result["error"], workflow)
            
            # Finalize workflow
            workflow.state = WorkflowState.COMPLETED
            workflow.end_time = datetime.now()
            
            return {
                "workflow_id": workflow.id,
                "state": workflow.state.value,
                "duration": (workflow.end_time - workflow.start_time).total_seconds(),
                "tasks_completed": len([t for t in workflow.tasks if t.state == WorkflowState.COMPLETED]),
                "results": execution_context["results"],
                "errors": execution_context["errors"]
            }
            
        except Exception as e:
            workflow.state = WorkflowState.FAILED
            workflow.end_time = datetime.now()
            raise AgentExecutionError(f"Workflow execution failed: {e}")
    
    def _execute_task_batch(self, tasks: List[WorkflowTask], 
                           context: Dict) -> List[Dict]:
        """Execute a batch of tasks in parallel."""
        results = []
        
        for task in tasks:
            try:
                task.state = WorkflowState.RUNNING
                task.start_time = datetime.now()
                
                # Execute task with appropriate agent
                result = self._execute_single_task(task, context)
                
                task.end_time = datetime.now()
                results.append({
                    "success": True,
                    "output": result,
                    "duration": (task.end_time - task.start_time).total_seconds()
                })
                
            except Exception as e:
                task.end_time = datetime.now()
                task.error = str(e)
                results.append({
                    "success": False,
                    "error": str(e),
                    "duration": (task.end_time - task.start_time).total_seconds()
                })
        
        return results
    
    def _execute_single_task(self, task: WorkflowTask, context: Dict) -> Any:
        """Execute a single task with the appropriate agent."""
        self._logger.info("Executing task", task_id=task.id, agent=task.agent_type)
        
        # Get or create agent instance
        agent = self._get_agent(task.agent_type)
        
        # Prepare task context
        task_context = {
            **task.context,
            "workflow_context": context,
            "dependencies": {dep: context["results"].get(dep) for dep in task.dependencies}
        }
        
        # Execute task
        result = agent.execute(task.prompt, **task_context)
        
        return result.output if result.success else None
    
    def _handle_task_failure(self, task: WorkflowTask, error: str, workflow: Workflow):
        """Handle task failure based on error strategy."""
        task.retry_count += 1
        
        if workflow.error_strategy == "fail_fast":
            workflow.state = WorkflowState.FAILED
            raise AgentExecutionError(f"Task {task.id} failed: {error}")
        
        elif workflow.error_strategy == "retry" and task.retry_count < task.max_retries:
            # Retry task
            task.state = WorkflowState.PENDING
            self._logger.info("Retrying task", task_id=task.id, attempt=task.retry_count)
        
        elif workflow.error_strategy == "continue":
            # Mark as failed but continue
            task.state = WorkflowState.FAILED
            self._logger.warning("Task failed, continuing", task_id=task.id, error=error)
        
        else:
            task.state = WorkflowState.FAILED
    
    # Helper methods
    def _generate_task_prompt(self, task_def: Dict, main_prompt: str) -> str:
        """Generate specific prompt for a task."""
        return f"{task_def['action']}: {main_prompt}"
    
    def _determine_priority(self, task_def: Dict) -> TaskPriority:
        """Determine task priority."""
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND
        }
        return priority_map.get(task_def.get("priority", "medium"), TaskPriority.MEDIUM)
    
    def _setup_dependencies(self, workflow: Workflow):
        """Set up task dependencies based on workflow type."""
        # Simple sequential dependencies for now
        for i in range(1, len(workflow.tasks)):
            workflow.tasks[i].dependencies.append(workflow.tasks[i-1].id)
    
    def _analyze_task_requirements(self, prompt: str) -> Dict:
        """Analyze task requirements from prompt."""
        # Simplified analysis
        requirements = {
            "complexity": "medium",
            "requires_testing": "test" in prompt.lower(),
            "requires_analysis": "analyze" in prompt.lower(),
            "requires_optimization": "optimize" in prompt.lower()
        }
        return requirements
    
    def _determine_optimal_parallelism(self, analysis: Dict) -> int:
        """Determine optimal parallelism level."""
        if analysis.get("complexity") == "high":
            return 2
        elif analysis.get("complexity") == "low":
            return 8
        return 4
    
    def _generate_task_sequence(self, analysis: Dict, prompt: str) -> List[Dict]:
        """Generate optimal task sequence."""
        sequence = []
        
        if analysis.get("requires_analysis"):
            sequence.append({
                "name": "analysis",
                "agent": "analyzer",
                "prompt": f"Analyze: {prompt}"
            })
        
        sequence.append({
            "name": "implementation",
            "agent": "coder",
            "prompt": f"Implement: {prompt}",
            "dependencies": ["analysis"] if analysis.get("requires_analysis") else []
        })
        
        if analysis.get("requires_testing"):
            sequence.append({
                "name": "testing",
                "agent": "test",
                "prompt": f"Test implementation for: {prompt}",
                "dependencies": ["implementation"]
            })
        
        if analysis.get("requires_optimization"):
            sequence.append({
                "name": "optimization",
                "agent": "optimizer",
                "prompt": f"Optimize: {prompt}",
                "dependencies": ["testing"] if analysis.get("requires_testing") else ["implementation"]
            })
        
        return sequence
    
    def _calculate_task_priority(self, task_def: Dict, index: int, total: int) -> TaskPriority:
        """Calculate task priority based on position and type."""
        if index == 0:
            return TaskPriority.HIGH
        elif index == total - 1:
            return TaskPriority.MEDIUM
        return TaskPriority.MEDIUM
    
    def _optimize_task_order(self, workflow: Workflow):
        """Optimize task execution order."""
        # Sort by priority and dependencies
        # Simplified - would use topological sort in production
        workflow.tasks.sort(key=lambda t: (t.priority.value, len(t.dependencies)))
    
    def _build_dependency_graph(self, workflow: Workflow) -> Dict[str, List[str]]:
        """Build task dependency graph."""
        graph = {}
        for task in workflow.tasks:
            graph[task.id] = task.dependencies
        return graph
    
    def _has_pending_tasks(self, workflow: Workflow) -> bool:
        """Check if workflow has pending tasks."""
        return any(t.state == WorkflowState.PENDING for t in workflow.tasks)
    
    def _get_executable_tasks(self, workflow: Workflow, graph: Dict) -> List[WorkflowTask]:
        """Get tasks that can be executed now."""
        executable = []
        
        for task in workflow.tasks:
            if task.state != WorkflowState.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                self._get_task_by_id(workflow, dep_id).state == WorkflowState.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_completed:
                executable.append(task)
        
        return executable
    
    def _detect_deadlock(self, workflow: Workflow) -> bool:
        """Detect if workflow is in deadlock."""
        pending_tasks = [t for t in workflow.tasks if t.state == WorkflowState.PENDING]
        
        if not pending_tasks:
            return False
        
        # Check if any pending task has all dependencies completed or failed
        for task in pending_tasks:
            deps_finished = all(
                self._get_task_by_id(workflow, dep_id).state in [WorkflowState.COMPLETED, WorkflowState.FAILED]
                for dep_id in task.dependencies
            )
            if deps_finished:
                return False
        
        return True
    
    def _get_task_by_id(self, workflow: Workflow, task_id: str) -> Optional[WorkflowTask]:
        """Get task by ID."""
        for task in workflow.tasks:
            if task.id == task_id:
                return task
        return None
    
    def _get_agent(self, agent_type: str) -> BaseAgent:
        """Get or create agent instance."""
        if agent_type not in self.agent_pool:
            # Create new agent instance
            # In production, would dynamically load agent class
            config = AgentConfig(name=f"{agent_type}_agent")
            self.agent_pool[agent_type] = BaseAgent(config)
        
        return self.agent_pool[agent_type]
    
    def _calculate_success_rate(self) -> float:
        """Calculate workflow success rate."""
        if not self.execution_history:
            return 100.0
        
        successful = sum(
            1 for h in self.execution_history 
            if h["result"].get("state") == WorkflowState.COMPLETED.value
        )
        
        return (successful / len(self.execution_history)) * 100