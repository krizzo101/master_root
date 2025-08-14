"""ExecutorAgent - General purpose task executor."""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import time
import json
import structlog

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult
from ..tools import tool_registry


logger = structlog.get_logger()


class ExecutionMode(Enum):
    """Execution modes for tasks."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ASYNC = "async"
    BATCH = "batch"


@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata or {}
        }


class ExecutorAgent(BaseAgent):
    """General purpose task executor with tool integration."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize executor agent."""
        super().__init__(config or AgentConfig(
            name="ExecutorAgent",
            description="General purpose task executor",
            capabilities=["execution", "tool_use", "api_calls", "orchestration"],
            max_retries=3,
            timeout=300
        ))
        self.tools = {}
        self.execution_history = []
        self.max_history = 100
    
    def initialize(self) -> bool:
        """Initialize the executor agent."""
        # Load available tools from registry
        self._load_tools()
        logger.info("executor_agent_initialized", agent=self.config.name, tools_count=len(self.tools))
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with appropriate strategy."""
        action = task.get("action", "run")
        
        if action == "run":
            return self._execute_task(task)
        elif action == "batch":
            return self._execute_batch(task)
        elif action == "chain":
            return self._execute_chain(task)
        elif action == "parallel":
            return self._execute_parallel(task)
        elif action == "tool":
            return self._execute_tool(task)
        elif action == "api":
            return self._execute_api(task)
        elif action == "history":
            return self._get_history(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def run(self, 
            command: str, 
            params: Optional[Dict[str, Any]] = None,
            mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> ExecutionResult:
        """Execute a command or task."""
        result = self.execute({
            "action": "run",
            "command": command,
            "params": params or {},
            "mode": mode.value
        })
        
        if "error" in result:
            return ExecutionResult(success=False, result=None, error=result["error"])
        
        return result["execution_result"]
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        command = task.get("command", "")
        params = task.get("params", {})
        context = task.get("context", {})
        
        if not command:
            return {"error": "Command is required"}
        
        start_time = time.time()
        
        try:
            # Determine execution strategy
            if command.startswith("tool:"):
                # Execute tool
                tool_name = command[5:]
                result = self._run_tool(tool_name, params)
            elif command.startswith("api:"):
                # Execute API call
                api_endpoint = command[4:]
                result = self._call_api(api_endpoint, params)
            elif command.startswith("agent:"):
                # Execute via another agent
                agent_name = command[6:]
                result = self._run_agent(agent_name, params)
            elif command.startswith("script:"):
                # Execute script
                script_path = command[7:]
                result = self._run_script(script_path, params)
            else:
                # Generic execution
                result = self._run_generic(command, params, context)
            
            duration = time.time() - start_time
            
            execution_result = ExecutionResult(
                success=True,
                result=result,
                duration=duration,
                metadata={"command": command, "params": params}
            )
            
            # Track in history
            self._track_execution(execution_result)
            
            logger.info(
                "task_executed",
                command=command,
                success=True,
                duration=duration
            )
            
            return {"execution_result": execution_result}
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            execution_result = ExecutionResult(
                success=False,
                result=None,
                error=error_msg,
                duration=duration,
                metadata={"command": command, "params": params}
            )
            
            # Track failure
            self._track_execution(execution_result)
            
            logger.error(
                "task_execution_failed",
                command=command,
                error=error_msg,
                duration=duration
            )
            
            return {"error": error_msg, "execution_result": execution_result}
    
    def _execute_batch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple tasks in batch."""
        tasks = task.get("tasks", [])
        stop_on_error = task.get("stop_on_error", False)
        
        if not tasks:
            return {"error": "Tasks list is required"}
        
        results = []
        total_duration = 0
        
        for i, sub_task in enumerate(tasks):
            result = self._execute_task(sub_task)
            
            if "execution_result" in result:
                exec_result = result["execution_result"]
                results.append(exec_result)
                total_duration += exec_result.duration
                
                if not exec_result.success and stop_on_error:
                    logger.warning(f"Batch execution stopped at task {i+1} due to error")
                    break
            else:
                # Error in execution
                results.append(ExecutionResult(
                    success=False,
                    result=None,
                    error=result.get("error", "Unknown error")
                ))
                
                if stop_on_error:
                    break
        
        success_count = sum(1 for r in results if r.success)
        
        return {
            "results": results,
            "total_tasks": len(tasks),
            "successful": success_count,
            "failed": len(results) - success_count,
            "total_duration": total_duration
        }
    
    def _execute_chain(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks in a chain (output of one is input to next)."""
        chain = task.get("chain", [])
        initial_input = task.get("initial_input", {})
        
        if not chain:
            return {"error": "Chain list is required"}
        
        current_input = initial_input
        results = []
        total_duration = 0
        
        for i, step in enumerate(chain):
            # Prepare task with current input
            step_task = {
                "command": step.get("command", ""),
                "params": {**step.get("params", {}), **current_input},
                "context": step.get("context", {})
            }
            
            result = self._execute_task(step_task)
            
            if "execution_result" in result:
                exec_result = result["execution_result"]
                results.append(exec_result)
                total_duration += exec_result.duration
                
                if exec_result.success:
                    # Use output as input for next step
                    if isinstance(exec_result.result, dict):
                        current_input = exec_result.result
                    else:
                        current_input = {"result": exec_result.result}
                else:
                    # Chain broken due to error
                    logger.error(f"Chain execution failed at step {i+1}")
                    break
            else:
                # Error in execution
                results.append(ExecutionResult(
                    success=False,
                    result=None,
                    error=result.get("error", "Unknown error")
                ))
                break
        
        # Final result is the last successful result
        final_result = results[-1] if results else None
        
        return {
            "chain_result": final_result,
            "step_results": results,
            "steps_completed": len(results),
            "total_steps": len(chain),
            "total_duration": total_duration
        }
    
    def _execute_parallel(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks in parallel (simplified synchronous version)."""
        tasks = task.get("tasks", [])
        
        if not tasks:
            return {"error": "Tasks list is required"}
        
        # For now, execute sequentially but track as parallel
        # Real parallel execution would use threading/multiprocessing
        results = []
        start_time = time.time()
        
        for sub_task in tasks:
            result = self._execute_task(sub_task)
            if "execution_result" in result:
                results.append(result["execution_result"])
            else:
                results.append(ExecutionResult(
                    success=False,
                    result=None,
                    error=result.get("error", "Unknown error")
                ))
        
        total_duration = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        
        return {
            "parallel_results": results,
            "total_tasks": len(tasks),
            "successful": success_count,
            "failed": len(results) - success_count,
            "total_duration": total_duration
        }
    
    def _execute_tool(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool."""
        tool_name = task.get("tool_name", "")
        params = task.get("params", {})
        
        if not tool_name:
            return {"error": "Tool name is required"}
        
        result = self._run_tool(tool_name, params)
        
        return {
            "tool_result": result,
            "tool": tool_name
        }
    
    def _execute_api(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an API call."""
        endpoint = task.get("endpoint", "")
        method = task.get("method", "GET")
        params = task.get("params", {})
        headers = task.get("headers", {})
        
        if not endpoint:
            return {"error": "API endpoint is required"}
        
        result = self._call_api(endpoint, params, method, headers)
        
        return {
            "api_result": result,
            "endpoint": endpoint,
            "method": method
        }
    
    def _load_tools(self):
        """Load available tools from registry."""
        # Get tools from the tool registry
        available_tools = tool_registry.get_tools()
        
        for tool_name, tool_def in available_tools.items():
            self.tools[tool_name] = tool_def
        
        # Add built-in tools
        self.tools.update({
            "echo": {"function": lambda x: x, "description": "Echo input"},
            "eval": {"function": lambda expr: eval(expr), "description": "Evaluate expression"},
            "format": {"function": lambda template, **kwargs: template.format(**kwargs), 
                      "description": "Format string template"}
        })
    
    def _run_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Run a specific tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        if isinstance(tool, dict) and "function" in tool:
            # Built-in tool
            func = tool["function"]
            if callable(func):
                return func(**params) if params else func()
        elif hasattr(tool, "execute"):
            # Tool with execute method
            return tool.execute(params)
        else:
            raise ValueError(f"Tool '{tool_name}' is not executable")
    
    def _call_api(self, endpoint: str, params: Dict[str, Any], 
                  method: str = "GET", headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make an API call (simplified mock implementation)."""
        # This would normally use requests or httpx
        # For now, return mock response
        return {
            "status": 200,
            "endpoint": endpoint,
            "method": method,
            "response": {
                "message": "Mock API response",
                "params": params
            }
        }
    
    def _run_agent(self, agent_name: str, params: Dict[str, Any]) -> Any:
        """Run another agent (simplified)."""
        # This would normally look up and execute another agent
        # For now, return mock response
        return {
            "agent": agent_name,
            "result": f"Mock result from {agent_name}",
            "params": params
        }
    
    def _run_script(self, script_path: str, params: Dict[str, Any]) -> Any:
        """Run a script (simplified)."""
        # This would normally execute a script file
        # For now, return mock response
        return {
            "script": script_path,
            "result": "Mock script execution result",
            "params": params
        }
    
    def _run_generic(self, command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Run generic command."""
        # Generic command execution
        # This could be enhanced with command parsers, interpreters, etc.
        return {
            "command": command,
            "params": params,
            "context": context,
            "result": f"Executed: {command}"
        }
    
    def _track_execution(self, result: ExecutionResult):
        """Track execution in history."""
        self.execution_history.append({
            "timestamp": time.time(),
            "result": result.to_dict()
        })
        
        # Limit history size
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
    
    def _get_history(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution history."""
        limit = task.get("limit", 10)
        filter_success = task.get("filter_success")
        
        history = self.execution_history[-limit:]
        
        if filter_success is not None:
            history = [
                h for h in history 
                if h["result"]["success"] == filter_success
            ]
        
        return {
            "history": history,
            "total_executions": len(self.execution_history)
        }
    
    def shutdown(self) -> bool:
        """Shutdown the executor agent."""
        logger.info("executor_agent_shutdown", 
                   total_executions=len(self.execution_history))
        self.execution_history.clear()
        self.tools.clear()
        return True