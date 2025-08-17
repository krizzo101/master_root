# SDLC Orchestration: Practical Implementation Guide

## Quick Start

### 1. Basic Setup
```bash
# Install the orchestrator
cd /home/opsvi/master_root/libs/opsvi-orchestrator
pip install -e .

# Set environment variables
export SDLC_ORCHESTRATOR_HOME=/home/opsvi/master_root
export SDLC_MAX_PARALLEL=3
export SDLC_SESSION_EXPORT=true
```

### 2. Simple Phase Execution
```python
from opsvi_orchestrator import SDLCOrchestrator

# Run discovery phase with default settings
orchestrator = SDLCOrchestrator('discovery')
report = orchestrator.execute_phase()

print(f"Success: {report['success_rate']}%")
print(f"Duration: {report['duration']}s")
```

## Core Concepts

### Micro-Task Definition
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MicroTask:
    id: str                          # Unique identifier
    name: str                        # Human-readable name
    phase: str                       # SDLC phase
    wave: int                        # Execution wave (1, 2, 3...)
    tools: List[str]                 # Required tools
    outputs: List[str]               # Expected outputs
    timeout_seconds: int = 300      # Max execution time
    dependencies: List[str] = None   # Task dependencies
    retry_count: int = 3            # Retry attempts
    metadata: dict = None           # Additional config
```

### Wave-Based Execution
```python
# Tasks execute in waves with dependencies
Wave 1: Independent tasks (no dependencies)
Wave 2: Tasks that depend on Wave 1
Wave 3: Integration tasks depending on Wave 1+2
```

## Implementation Patterns

### Pattern 1: Custom Task Decomposition
```python
def create_custom_decomposition(phase: str) -> List[MicroTask]:
    """Create custom task breakdown for a phase."""

    if phase == "development":
        return [
            # Wave 1: Architecture
            MicroTask(
                id="arch_design",
                name="Design Architecture",
                phase="development",
                wave=1,
                tools=["file_writer", "mcp__thinking__sequentialthinking"],
                outputs=["docs/architecture.md"],
                timeout_seconds=180
            ),
            MicroTask(
                id="interface_design",
                name="Define Interfaces",
                phase="development",
                wave=1,
                tools=["file_writer"],
                outputs=["src/interfaces.py"],
                timeout_seconds=180
            ),

            # Wave 2: Implementation
            MicroTask(
                id="core_impl",
                name="Implement Core Logic",
                phase="development",
                wave=2,
                dependencies=["arch_design", "interface_design"],
                tools=["file_writer", "multi_edit"],
                outputs=["src/core.py"],
                timeout_seconds=300
            ),

            # Wave 3: Testing
            MicroTask(
                id="unit_tests",
                name="Write Unit Tests",
                phase="development",
                wave=3,
                dependencies=["core_impl"],
                tools=["file_writer", "test_runner"],
                outputs=["tests/test_core.py"],
                timeout_seconds=240
            )
        ]
```

### Pattern 2: Intelligent Mode Selection
```python
class ExecutionModeSelector:
    """Select optimal execution mode for tasks."""

    def select_mode(self, task: MicroTask) -> str:
        """
        Returns: 'task', 'mcp', or 'direct'
        """
        # Complex, long-running tasks -> MCP
        if task.timeout_seconds > 300:
            return "mcp"

        # Tasks requiring specific tools -> MCP
        if any(tool in task.tools for tool in [
            "test_runner", "deployment_tool", "database_tool"
        ]):
            return "mcp"

        # Lightweight file operations -> Task
        if any(tool in task.tools for tool in [
            "file_writer", "file_reader", "grep", "glob"
        ]):
            return "task"

        # Ultra-fast operations -> Direct
        if task.timeout_seconds < 60:
            return "direct"

        # Default to Task for general work
        return "task"
```

### Pattern 3: Continuous Validation
```python
class WaveValidator:
    """Validate outputs after each wave."""

    def validate_wave(self, wave_num: int, results: List[dict]) -> dict:
        """
        Validate all results from a wave.
        Returns validation report with failures.
        """
        validation_report = {
            "wave": wave_num,
            "passed": [],
            "failed": [],
            "warnings": []
        }

        for result in results:
            task = result["task"]

            # Check file existence
            for output_file in task.outputs:
                if not Path(output_file).exists():
                    validation_report["failed"].append({
                        "task": task.id,
                        "error": f"Missing output: {output_file}",
                        "severity": "critical"
                    })
                else:
                    validation_report["passed"].append({
                        "task": task.id,
                        "output": output_file
                    })

            # Check Python syntax if applicable
            if any(f.endswith('.py') for f in task.outputs):
                for py_file in [f for f in task.outputs if f.endswith('.py')]:
                    if Path(py_file).exists():
                        code = Path(py_file).read_text()
                        try:
                            compile(code, py_file, 'exec')
                        except SyntaxError as e:
                            validation_report["warnings"].append({
                                "task": task.id,
                                "warning": f"Syntax error in {py_file}: {e}"
                            })

        return validation_report
```

### Pattern 4: Automatic Correction
```python
class CorrectionGenerator:
    """Generate correction tasks for failures."""

    def generate_corrections(self, failures: List[dict]) -> List[MicroTask]:
        """
        Create micro-tasks to fix failures.
        """
        corrections = []

        for failure in failures:
            if "Missing output" in failure["error"]:
                # Create task to generate missing file
                corrections.append(MicroTask(
                    id=f"fix_{failure['task']}",
                    name=f"Generate {failure['error'].split(': ')[1]}",
                    phase="correction",
                    wave=1,
                    tools=["file_writer"],
                    outputs=[failure['error'].split(': ')[1]],
                    timeout_seconds=180,
                    metadata={"correction_for": failure['task']}
                ))

            elif "Syntax error" in failure.get("warning", ""):
                # Create task to fix syntax
                corrections.append(MicroTask(
                    id=f"fix_syntax_{failure['task']}",
                    name=f"Fix syntax in {failure['task']}",
                    phase="correction",
                    wave=1,
                    tools=["file_editor", "python_linter"],
                    outputs=[],
                    timeout_seconds=120,
                    metadata={"fix_type": "syntax"}
                ))

        return corrections
```

## Advanced Integration

### Task Tool Callback Integration
```python
def create_task_tool_integration():
    """Integrate with Claude's Task tool."""

    def task_callback(description: str, subagent_type: str, prompt: str):
        # Map to actual Task tool
        from claude_tools import Task

        result = Task(
            description=description,
            subagent_type=subagent_type,
            prompt=prompt
        )

        # Parse and return result
        return {
            "status": "success" if result else "failure",
            "output": result,
            "metadata": {
                "agent": subagent_type,
                "timestamp": datetime.now().isoformat()
            }
        }

    return task_callback
```

### MCP Server Integration
```python
def create_mcp_integration():
    """Integrate with MCP server."""

    def mcp_callback(task: str, **kwargs):
        # Use the MCP tool
        result = mcp__claude_code_wrapper__claude_run(
            task=task,
            outputFormat="json",
            permissionMode="bypassPermissions",
            verbose=True,
            **kwargs
        )

        # Extract metrics and return
        return {
            "status": result.get("status", "unknown"),
            "output": result.get("output", ""),
            "metrics": {
                "duration_ms": result.get("duration_ms", 0),
                "cost_usd": result.get("total_cost_usd", 0),
                "tokens": result.get("usage", {})
            }
        }

    return mcp_callback
```

### Knowledge Base Integration
```python
class KnowledgeIntegration:
    """Integrate with Neo4j knowledge base."""

    def query_patterns(self, task: MicroTask) -> List[dict]:
        """Find relevant patterns for task."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_type = 'CODE_PATTERN'
          AND ANY(tag IN $tags WHERE tag IN k.tags)
        RETURN k
        ORDER BY k.confidence_score DESC
        LIMIT 5
        """

        # Extract tags from task
        tags = self._extract_tags(task)

        # Query knowledge base
        results = mcp__db__read_neo4j_cypher(
            query=query,
            params={"tags": tags}
        )

        return results

    def store_success_pattern(self, task: MicroTask, output: dict):
        """Store successful pattern for future use."""
        mcp__knowledge__knowledge_store(
            knowledge_type="CODE_PATTERN",
            content=f"Successful {task.name} implementation",
            context={
                "task": task.to_dict(),
                "output": output,
                "tools_used": task.tools
            },
            confidence_score=0.9,
            tags=[task.phase, task.name] + task.tools
        )
```

## Monitoring & Observability

### Real-Time Monitoring
```python
class OrchestrationMonitor:
    """Monitor active orchestration."""

    def __init__(self, executor):
        self.executor = executor
        self.start_time = datetime.now()

    def get_status(self) -> dict:
        """Get current orchestration status."""
        active = self.executor.get_active_sessions()

        return {
            "active_tasks": len(active),
            "runtime": (datetime.now() - self.start_time).seconds,
            "tasks": [
                {
                    "name": session["task_name"],
                    "duration": session["duration_so_far"],
                    "mode": session["mode"]
                }
                for session in active
            ]
        }

    def print_dashboard(self):
        """Print monitoring dashboard."""
        status = self.get_status()

        print("=" * 60)
        print("ORCHESTRATION DASHBOARD")
        print("=" * 60)
        print(f"Runtime: {status['runtime']}s")
        print(f"Active Tasks: {status['active_tasks']}")
        print()

        for task in status['tasks']:
            print(f"  • {task['name']:<30} [{task['mode']:>8}] {task['duration']:.1f}s")
```

### Session Analysis
```python
def analyze_session_exports(session_dir: Path) -> dict:
    """Analyze exported sessions for insights."""

    sessions = list(session_dir.glob("*.json"))

    analysis = {
        "total_sessions": len(sessions),
        "success_rate": 0,
        "avg_duration": 0,
        "mode_distribution": {},
        "failure_patterns": []
    }

    durations = []
    successes = 0

    for session_file in sessions:
        with open(session_file) as f:
            data = json.load(f)

        # Track success
        if not data.get("error"):
            successes += 1
        else:
            # Analyze failure
            analysis["failure_patterns"].append({
                "task": data["task"]["name"],
                "error": data["error"]
            })

        # Track duration
        if data.get("execution", {}).get("duration_seconds"):
            durations.append(data["execution"]["duration_seconds"])

        # Track mode
        mode = data.get("execution", {}).get("mode", "unknown")
        analysis["mode_distribution"][mode] = \
            analysis["mode_distribution"].get(mode, 0) + 1

    # Calculate aggregates
    analysis["success_rate"] = (successes / len(sessions)) * 100 if sessions else 0
    analysis["avg_duration"] = sum(durations) / len(durations) if durations else 0

    return analysis
```

## Testing Framework

### Unit Tests for Orchestration
```python
import unittest
from unittest.mock import Mock, patch

class TestOrchestration(unittest.TestCase):
    """Test orchestration components."""

    def test_task_decomposition(self):
        """Test phase decomposition."""
        decomposer = TaskDecomposer()
        tasks = decomposer.decompose_phase("discovery")

        # Verify wave structure
        waves = {}
        for task in tasks:
            if task.wave not in waves:
                waves[task.wave] = []
            waves[task.wave].append(task)

        # Check wave 1 has no dependencies
        for task in waves.get(1, []):
            self.assertIsNone(task.dependencies)

        # Check later waves have dependencies
        for wave_num in range(2, max(waves.keys()) + 1):
            for task in waves.get(wave_num, []):
                self.assertIsNotNone(task.dependencies)

    def test_mode_selection(self):
        """Test execution mode selection."""
        selector = ExecutionModeSelector()

        # Test complex task -> MCP
        complex_task = MicroTask(
            id="complex",
            name="Complex Task",
            phase="test",
            wave=1,
            tools=["test_runner"],
            outputs=[],
            timeout_seconds=600
        )
        self.assertEqual(selector.select_mode(complex_task), "mcp")

        # Test simple task -> Task
        simple_task = MicroTask(
            id="simple",
            name="Simple Task",
            phase="test",
            wave=1,
            tools=["file_writer"],
            outputs=["test.txt"],
            timeout_seconds=180
        )
        self.assertEqual(selector.select_mode(simple_task), "task")

    @patch('executor.Task')
    def test_task_execution(self, mock_task):
        """Test task tool execution."""
        mock_task.return_value = {"status": "success"}

        executor = RealWorldExecutor(
            task_tool_callback=lambda **kwargs: mock_task(**kwargs)
        )

        task = MicroTask(
            id="test",
            name="Test Task",
            phase="test",
            wave=1,
            tools=["file_writer"],
            outputs=["test.txt"],
            timeout_seconds=180
        )

        context = executor.execute_with_monitoring(
            task=task,
            mode="task",
            prompt="Test execution"
        )

        self.assertIsNone(context.error)
        self.assertEqual(context.output["status"], "success")
```

## Performance Optimization

### Caching Strategy
```python
class TaskCache:
    """Cache task results for reuse."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, task: MicroTask) -> str:
        """Generate cache key for task."""
        import hashlib

        # Create unique key from task properties
        key_parts = [
            task.id,
            task.phase,
            str(task.wave),
            str(sorted(task.tools)),
            str(sorted(task.outputs))
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, task: MicroTask) -> Optional[dict]:
        """Get cached result if available."""
        cache_key = self.get_cache_key(task)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            # Check cache age
            age = time.time() - cache_file.stat().st_mtime
            if age < 3600:  # 1 hour cache
                with open(cache_file) as f:
                    return json.load(f)

        return None

    def set(self, task: MicroTask, result: dict):
        """Cache task result."""
        cache_key = self.get_cache_key(task)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, 'w') as f:
            json.dump(result, f)
```

### Resource Throttling
```python
class ResourceManager:
    """Manage resource usage."""

    def __init__(self, max_parallel: int = 3, max_cost_usd: float = 1.0):
        self.max_parallel = max_parallel
        self.max_cost_usd = max_cost_usd
        self.current_cost = 0.0
        self.semaphore = threading.Semaphore(max_parallel)

    def acquire(self, estimated_cost: float = 0.05) -> bool:
        """Acquire resources for task execution."""
        if self.current_cost + estimated_cost > self.max_cost_usd:
            return False

        self.semaphore.acquire()
        self.current_cost += estimated_cost
        return True

    def release(self, actual_cost: float = 0.05):
        """Release resources after task completion."""
        self.semaphore.release()
        # Update with actual cost
        self.current_cost = self.current_cost - 0.05 + actual_cost
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Timeout Issues
```python
# Problem: Tasks still timing out
# Solution: Further decompose tasks
def handle_timeout(task: MicroTask) -> List[MicroTask]:
    """Break down task that timed out."""
    return [
        MicroTask(
            id=f"{task.id}_part{i}",
            name=f"{task.name} Part {i}",
            phase=task.phase,
            wave=task.wave,
            tools=task.tools,
            outputs=[task.outputs[i]] if i < len(task.outputs) else [],
            timeout_seconds=task.timeout_seconds // 2
        )
        for i in range(2)
    ]
```

#### 2. Dependency Failures
```python
# Problem: Dependent task fails due to missing input
# Solution: Validate dependencies before execution
def validate_dependencies(task: MicroTask, completed_tasks: dict) -> bool:
    """Check if all dependencies are satisfied."""
    for dep_id in task.dependencies or []:
        if dep_id not in completed_tasks:
            return False
        if completed_tasks[dep_id].get("status") != "success":
            return False
    return True
```

#### 3. Mode Selection Issues
```python
# Problem: Wrong mode selected for task
# Solution: Override mode selection
task.metadata = {"force_mode": "mcp"}  # Force MCP mode
```

## Best Practices

1. **Keep Tasks Focused**: Each task should do ONE thing well
2. **Define Clear Outputs**: Specify exact file paths and formats
3. **Use Wave Dependencies**: Don't over-constrain with task-level deps
4. **Monitor Continuously**: Watch active sessions during execution
5. **Cache Aggressively**: Reuse successful results when possible
6. **Validate Early**: Check outputs immediately after each wave
7. **Log Everything**: Export sessions for debugging and analysis
8. **Handle Failures Gracefully**: Use correction agents for recovery

## Next Steps

1. Review the [orchestration examples](./example_usage.py)
2. Configure your [orchestrator settings](./orchestrator_config.yaml)
3. Run a test phase: `python -m opsvi_orchestrator.test_run`
4. Monitor execution in real-time
5. Analyze session exports for optimization opportunities

---

This guide provides practical patterns for implementing and extending the SDLC Orchestration System. For additional support, consult the architecture documentation or session analysis tools.
