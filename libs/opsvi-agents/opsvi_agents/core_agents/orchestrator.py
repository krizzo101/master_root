"""OrchestratorAgent - Multi-agent coordination."""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
import structlog

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult


logger = structlog.get_logger()


class CoordinationStrategy(Enum):
    """Agent coordination strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"
    ROUND_ROBIN = "round_robin"


class AgentRole(Enum):
    """Roles in orchestration."""
    LEADER = "leader"
    WORKER = "worker"
    VALIDATOR = "validator"
    AGGREGATOR = "aggregator"
    MONITOR = "monitor"


@dataclass
class AgentTask:
    """Task assigned to an agent."""
    id: str
    agent_id: str
    task: Dict[str, Any]
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task": self.task,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status,
            "error": self.error,
            "duration": self.end_time - self.start_time if self.end_time and self.start_time else None
        }


@dataclass
class Workflow:
    """Orchestrated workflow."""
    id: str
    name: str
    strategy: CoordinationStrategy
    tasks: List[AgentTask] = field(default_factory=list)
    agents: Dict[str, AgentRole] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def add_task(self, task: AgentTask):
        """Add task to workflow."""
        self.tasks.append(task)
    
    def get_ready_tasks(self) -> List[AgentTask]:
        """Get tasks ready for execution."""
        ready = []
        completed_ids = {t.id for t in self.tasks if t.status == "completed"}
        
        for task in self.tasks:
            if task.status == "pending":
                if all(dep in completed_ids for dep in task.dependencies):
                    ready.append(task)
        
        return ready
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "strategy": self.strategy.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "agents": {k: v.value for k, v in self.agents.items()},
            "status": self.status,
            "duration": self.end_time - self.start_time if self.end_time and self.start_time else None
        }


@dataclass
class OrchestrationResult:
    """Result of orchestration."""
    workflow_id: str
    success: bool
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "results": self.results,
            "errors": self.errors,
            "metrics": self.metrics
        }


class OrchestratorAgent(BaseAgent):
    """Coordinates multiple agents to achieve complex goals."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize orchestrator agent."""
        super().__init__(config or AgentConfig(
            name="OrchestratorAgent",
            description="Multi-agent coordination",
            capabilities=["orchestrate", "coordinate", "delegate", "aggregate", "monitor"],
            max_retries=3,
            timeout=300
        ))
        self.workflows: Dict[str, Workflow] = {}
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._workflow_counter = 0
        self._task_counter = 0
    
    def initialize(self) -> bool:
        """Initialize the orchestrator agent."""
        logger.info("orchestrator_agent_initialized", agent=self.config.name)
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration task."""
        action = task.get("action", "orchestrate")
        
        if action == "orchestrate":
            return self._orchestrate_workflow(task)
        elif action == "coordinate":
            return self._coordinate_agents(task)
        elif action == "delegate":
            return self._delegate_task(task)
        elif action == "aggregate":
            return self._aggregate_results(task)
        elif action == "monitor":
            return self._monitor_workflow(task)
        elif action == "create_workflow":
            return self._create_workflow(task)
        elif action == "execute_workflow":
            return self._execute_workflow(task)
        elif action == "register_agent":
            return self._register_agent(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def orchestrate(self,
                   goal: str,
                   agents: List[BaseAgent],
                   strategy: CoordinationStrategy = CoordinationStrategy.PARALLEL) -> OrchestrationResult:
        """Orchestrate agents to achieve goal."""
        result = self.execute({
            "action": "orchestrate",
            "goal": goal,
            "agents": agents,
            "strategy": strategy.value
        })
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        return result["result"]
    
    def _orchestrate_workflow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a complete workflow."""
        goal = task.get("goal", "")
        agents = task.get("agents", [])
        strategy = task.get("strategy", "parallel")
        
        if not goal:
            return {"error": "Goal is required"}
        
        # Create workflow
        self._workflow_counter += 1
        workflow = Workflow(
            id=f"workflow_{self._workflow_counter}",
            name=goal,
            strategy=CoordinationStrategy[strategy.upper()]
        )
        
        # Register agents
        for i, agent in enumerate(agents):
            agent_id = f"agent_{i}"
            if isinstance(agent, BaseAgent):
                self.agent_registry[agent_id] = agent
                workflow.agents[agent_id] = AgentRole.WORKER
        
        # Decompose goal into tasks
        tasks = self._decompose_goal(goal, len(agents))
        
        # Create agent tasks
        for i, task_data in enumerate(tasks):
            self._task_counter += 1
            agent_task = AgentTask(
                id=f"task_{self._task_counter}",
                agent_id=f"agent_{i % len(agents)}",
                task=task_data,
                priority=i
            )
            workflow.add_task(agent_task)
        
        # Store workflow
        self.workflows[workflow.id] = workflow
        
        # Execute workflow
        result = self._execute_workflow_internal(workflow)
        
        logger.info("workflow_orchestrated",
                   workflow_id=workflow.id,
                   strategy=strategy,
                   tasks_count=len(tasks))
        
        return {
            "result": result,
            "workflow_id": workflow.id
        }
    
    def _coordinate_agents(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate agent activities."""
        agents = task.get("agents", [])
        coordination_type = task.get("coordination_type", "sync")
        
        if not agents:
            return {"error": "Agents are required"}
        
        coordination_result = {
            "coordinated_agents": len(agents),
            "type": coordination_type,
            "status": "success"
        }
        
        if coordination_type == "sync":
            # Synchronous coordination
            for agent_id in agents:
                if agent_id in self.agent_registry:
                    # Coordinate agent
                    pass
        elif coordination_type == "async":
            # Asynchronous coordination
            futures = []
            for agent_id in agents:
                if agent_id in self.agent_registry:
                    # Submit async task
                    future = self.executor.submit(self._coordinate_single_agent, agent_id)
                    futures.append(future)
            
            # Wait for completion
            for future in futures:
                future.result()
        
        return coordination_result
    
    def _delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate task to appropriate agent."""
        task_data = task.get("task")
        agent_id = task.get("agent_id")
        auto_select = task.get("auto_select", True)
        
        if not task_data:
            return {"error": "Task is required"}
        
        # Auto-select agent if needed
        if auto_select and not agent_id:
            agent_id = self._select_best_agent(task_data)
        
        if not agent_id or agent_id not in self.agent_registry:
            return {"error": f"Agent {agent_id} not found"}
        
        # Delegate to agent
        agent = self.agent_registry[agent_id]
        result = agent.execute(task_data)
        
        return {
            "delegated_to": agent_id,
            "result": result
        }
    
    def _aggregate_results(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        results = task.get("results", [])
        aggregation_type = task.get("aggregation_type", "merge")
        
        if not results:
            return {"error": "Results are required"}
        
        aggregated = {}
        
        if aggregation_type == "merge":
            # Merge all results
            for result in results:
                if isinstance(result, dict):
                    aggregated.update(result)
        elif aggregation_type == "vote":
            # Voting/consensus
            votes = {}
            for result in results:
                key = str(result)
                votes[key] = votes.get(key, 0) + 1
            aggregated = {"consensus": max(votes, key=votes.get)}
        elif aggregation_type == "average":
            # Average numerical results
            if all(isinstance(r, (int, float)) for r in results):
                aggregated = {"average": sum(results) / len(results)}
        elif aggregation_type == "collect":
            # Collect all results
            aggregated = {"all_results": results}
        
        return {
            "aggregated": aggregated,
            "aggregation_type": aggregation_type,
            "input_count": len(results)
        }
    
    def _monitor_workflow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor workflow execution."""
        workflow_id = task.get("workflow_id")
        
        if not workflow_id or workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        
        # Get workflow status
        status = {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "strategy": workflow.strategy.value,
            "progress": {
                "total_tasks": len(workflow.tasks),
                "completed": sum(1 for t in workflow.tasks if t.status == "completed"),
                "failed": sum(1 for t in workflow.tasks if t.status == "failed"),
                "pending": sum(1 for t in workflow.tasks if t.status == "pending"),
                "running": sum(1 for t in workflow.tasks if t.status == "running")
            },
            "agents": len(workflow.agents)
        }
        
        # Get running tasks
        running_tasks = [t.to_dict() for t in workflow.tasks if t.status == "running"]
        status["running_tasks"] = running_tasks
        
        return status
    
    def _create_workflow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        name = task.get("name", "Workflow")
        strategy = task.get("strategy", "parallel")
        tasks_data = task.get("tasks", [])
        
        self._workflow_counter += 1
        workflow = Workflow(
            id=f"workflow_{self._workflow_counter}",
            name=name,
            strategy=CoordinationStrategy[strategy.upper()]
        )
        
        # Add tasks
        for task_data in tasks_data:
            self._task_counter += 1
            agent_task = AgentTask(
                id=f"task_{self._task_counter}",
                agent_id=task_data.get("agent_id", "default"),
                task=task_data.get("task", {}),
                priority=task_data.get("priority", 0),
                dependencies=task_data.get("dependencies", [])
            )
            workflow.add_task(agent_task)
        
        # Store workflow
        self.workflows[workflow.id] = workflow
        
        return {
            "workflow": workflow.to_dict(),
            "workflow_id": workflow.id
        }
    
    def _execute_workflow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow_id = task.get("workflow_id")
        
        if not workflow_id or workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        result = self._execute_workflow_internal(workflow)
        
        return {
            "result": result.to_dict(),
            "workflow_id": workflow_id
        }
    
    def _register_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent."""
        agent_id = task.get("agent_id")
        agent = task.get("agent")
        role = task.get("role", "worker")
        
        if not agent_id:
            return {"error": "Agent ID is required"}
        
        if isinstance(agent, BaseAgent):
            self.agent_registry[agent_id] = agent
            
            return {
                "registered": True,
                "agent_id": agent_id,
                "role": role
            }
        
        return {"error": "Invalid agent"}
    
    def _execute_workflow_internal(self, workflow: Workflow) -> OrchestrationResult:
        """Execute workflow internally."""
        workflow.start_time = time.time()
        workflow.status = "running"
        
        result = OrchestrationResult(
            workflow_id=workflow.id,
            success=True
        )
        
        try:
            if workflow.strategy == CoordinationStrategy.SEQUENTIAL:
                self._execute_sequential(workflow, result)
            elif workflow.strategy == CoordinationStrategy.PARALLEL:
                self._execute_parallel(workflow, result)
            elif workflow.strategy == CoordinationStrategy.PIPELINE:
                self._execute_pipeline(workflow, result)
            else:
                self._execute_default(workflow, result)
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            workflow.status = "failed"
        
        workflow.end_time = time.time()
        workflow.status = "completed" if result.success else "failed"
        
        # Calculate metrics
        result.metrics["duration"] = workflow.end_time - workflow.start_time
        result.metrics["tasks_completed"] = sum(1 for t in workflow.tasks if t.status == "completed")
        result.metrics["tasks_failed"] = sum(1 for t in workflow.tasks if t.status == "failed")
        
        return result
    
    def _execute_sequential(self, workflow: Workflow, result: OrchestrationResult):
        """Execute tasks sequentially."""
        for task in workflow.tasks:
            task.start_time = time.time()
            task.status = "running"
            
            try:
                if task.agent_id in self.agent_registry:
                    agent = self.agent_registry[task.agent_id]
                    task.result = agent.execute(task.task)
                    task.status = "completed"
                    result.results[task.id] = task.result
                else:
                    task.status = "failed"
                    task.error = f"Agent {task.agent_id} not found"
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                result.errors.append(f"Task {task.id}: {e}")
            
            task.end_time = time.time()
    
    def _execute_parallel(self, workflow: Workflow, result: OrchestrationResult):
        """Execute tasks in parallel."""
        futures = []
        
        for task in workflow.tasks:
            if task.agent_id in self.agent_registry:
                agent = self.agent_registry[task.agent_id]
                future = self.executor.submit(self._execute_single_task, task, agent)
                futures.append((task, future))
        
        # Wait for all tasks
        for task, future in futures:
            try:
                task.result = future.result(timeout=30)
                task.status = "completed"
                result.results[task.id] = task.result
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                result.errors.append(f"Task {task.id}: {e}")
    
    def _execute_pipeline(self, workflow: Workflow, result: OrchestrationResult):
        """Execute tasks in pipeline fashion."""
        previous_result = None
        
        for task in workflow.tasks:
            task.start_time = time.time()
            task.status = "running"
            
            # Pass previous result as input
            if previous_result:
                task.task["input"] = previous_result
            
            try:
                if task.agent_id in self.agent_registry:
                    agent = self.agent_registry[task.agent_id]
                    task.result = agent.execute(task.task)
                    task.status = "completed"
                    result.results[task.id] = task.result
                    previous_result = task.result
                else:
                    task.status = "failed"
                    task.error = f"Agent {task.agent_id} not found"
                    break
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                result.errors.append(f"Task {task.id}: {e}")
                break
            
            task.end_time = time.time()
    
    def _execute_default(self, workflow: Workflow, result: OrchestrationResult):
        """Execute with default strategy."""
        self._execute_sequential(workflow, result)
    
    def _execute_single_task(self, task: AgentTask, agent: BaseAgent) -> Any:
        """Execute a single task."""
        task.start_time = time.time()
        task.status = "running"
        
        try:
            result = agent.execute(task.task)
            task.end_time = time.time()
            return result
        except Exception as e:
            task.end_time = time.time()
            raise e
    
    def _decompose_goal(self, goal: str, num_agents: int) -> List[Dict[str, Any]]:
        """Decompose goal into tasks."""
        tasks = []
        
        # Simple decomposition
        base_task = {"action": "process", "goal": goal}
        
        for i in range(min(num_agents, 3)):  # Limit to 3 tasks for simplicity
            task = base_task.copy()
            task["part"] = i + 1
            tasks.append(task)
        
        return tasks
    
    def _select_best_agent(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Select best agent for task."""
        # Simple selection - return first available agent
        if self.agent_registry:
            return list(self.agent_registry.keys())[0]
        return None
    
    def _coordinate_single_agent(self, agent_id: str) -> None:
        """Coordinate a single agent."""
        if agent_id in self.agent_registry:
            # Coordination logic
            pass
    
    def shutdown(self) -> bool:
        """Shutdown the orchestrator agent."""
        self.executor.shutdown(wait=True)
        logger.info("orchestrator_agent_shutdown",
                   workflows_count=len(self.workflows),
                   agents_count=len(self.agent_registry))
        self.workflows.clear()
        self.agent_registry.clear()
        return True