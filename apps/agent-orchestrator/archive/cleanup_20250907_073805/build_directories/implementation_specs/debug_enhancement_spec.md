# Debug Enhancement Specification

## Overview
This specification details comprehensive debug logging enhancements for the orchestrator system, providing visibility into variable values, subprocess commands, token flow, and error details.

## Debug Logging Architecture

### 1. Debug Levels

```python
class DebugLevel(Enum):
    """Debug verbosity levels"""
    OFF = 0      # No debug output
    BASIC = 1    # Basic flow and errors
    VERBOSE = 2  # Detailed variable values
    TRACE = 3    # Full execution trace including tokens
```

### 2. Debug Logger Setup

**File**: `src/generic_orchestrator.py`
**Location**: After line 18 (imports)

```python
# Enhanced debug logging setup
import inspect
from enum import Enum
from functools import wraps

class OrchestratorDebugger:
    """Centralized debug logging for orchestrator"""

    def __init__(self, level: int = 1, log_file: Optional[Path] = None):
        self.level = level
        self.logger = logging.getLogger("orchestrator.debug")

        # Setup file handler if specified
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"
                )
            )
            self.logger.addHandler(handler)

        self.logger.setLevel(logging.DEBUG if level > 0 else logging.INFO)

    def log_entry(self, func_name: str, **kwargs):
        """Log function entry with parameters"""
        if self.level >= 2:
            params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self.logger.debug(f"ENTRY: {func_name}({params})")

    def log_exit(self, func_name: str, result=None):
        """Log function exit with result"""
        if self.level >= 2:
            self.logger.debug(f"EXIT: {func_name} -> {result}")

    def log_variable(self, name: str, value: Any, sensitive: bool = False):
        """Log variable value"""
        if self.level >= 2:
            if sensitive and self.level < 3:
                value = "***REDACTED***"
            self.logger.debug(f"VAR: {name} = {value}")

    def log_subprocess(self, cmd: List[str], env: Dict, cwd: str = None):
        """Log subprocess execution details"""
        if self.level >= 1:
            self.logger.debug(f"EXEC: {' '.join(cmd)}")
            if self.level >= 2:
                self.logger.debug(f"  CWD: {cwd or 'default'}")
            if self.level >= 3:
                # Log environment (mask sensitive values)
                safe_env = self._mask_sensitive_env(env)
                self.logger.debug(f"  ENV: {safe_env}")

    def log_token_flow(self, action: str, token_idx: int, task_id: str):
        """Log token acquisition/release"""
        if self.level >= 2:
            self.logger.debug(f"TOKEN: {action} token[{token_idx}] for {task_id}")

    def log_error(self, error: Exception, context: str = ""):
        """Log detailed error information"""
        self.logger.error(f"ERROR in {context}: {type(error).__name__}: {error}")
        if self.level >= 2:
            import traceback
            self.logger.error(f"TRACE:\n{traceback.format_exc()}")

    def _mask_sensitive_env(self, env: Dict) -> Dict:
        """Mask sensitive environment variables"""
        sensitive_keys = ["TOKEN", "KEY", "PASSWORD", "SECRET", "API"]
        safe_env = {}
        for key, value in env.items():
            if any(s in key.upper() for s in sensitive_keys):
                safe_env[key] = "***REDACTED***"
            else:
                safe_env[key] = value
        return safe_env
```

### 3. Debug Decorator

**Add after OrchestratorDebugger class**:

```python
def debug_trace(debugger: OrchestratorDebugger):
    """Decorator to add debug tracing to methods"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature for logging
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Log entry
            debugger.log_entry(func.__name__, **bound.arguments)

            try:
                result = await func(*args, **kwargs)
                debugger.log_exit(func.__name__, result)
                return result
            except Exception as e:
                debugger.log_error(e, func.__name__)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            debugger.log_entry(func.__name__, **bound.arguments)

            try:
                result = func(*args, **kwargs)
                debugger.log_exit(func.__name__, result)
                return result
            except Exception as e:
                debugger.log_error(e, func.__name__)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
```

### 4. Integration with GenericOrchestrator

**Modify __init__ method (line 171)**:

```python
def __init__(
    self,
    output_dir: Path,
    max_parallel: int = 10,
    tokens: List[str] = None,
    use_optimizations: bool = True,
    # Debug parameters
    agent_debug_mode: bool = False,
    debug_level: int = 0,  # 0=off, 1=basic, 2=verbose, 3=trace
    debug_log_file: Optional[Path] = None,
    # ... other new parameters
):
    # Setup debug logging first
    self.debug_level = debug_level
    self.agent_debug_mode = agent_debug_mode

    # Initialize debugger
    debug_file = debug_log_file or (
        output_dir / "logs" / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    self.debugger = OrchestratorDebugger(debug_level, debug_file)

    # Log initialization
    self.debugger.log_entry("__init__",
        output_dir=output_dir,
        max_parallel=max_parallel,
        use_optimizations=use_optimizations,
        debug_level=debug_level
    )

    # ... rest of initialization
```

### 5. Enhanced execute_agent with Debug Logging

**Modify execute_agent method**:

```python
async def execute_agent(self, task: AgentTask) -> Dict:
    """Execute a single agent task with comprehensive debug logging."""

    session_id = str(uuid.uuid4())

    # Debug: Log task execution start
    self.debugger.log_entry("execute_agent",
        task_id=task.task_id,
        task_type=task.task_type,
        session_id=session_id
    )

    # Debug: Log task details
    self.debugger.log_variable("task.prompt", task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt)
    self.debugger.log_variable("task.dependencies", task.dependencies)
    self.debugger.log_variable("task.context", task.context)

    # ... pre-execution hook ...

    # Build command with debug logging
    cmd = self.claude_cmd.copy()

    # Add debug flag if enabled
    if self.agent_debug_mode:
        cmd.append("--debug")
        self.debugger.log_variable("agent_debug_mode", True)

    # Debug: Log command construction
    self.debugger.log_variable("base_command", cmd)

    # Get token with debug logging
    token, token_idx = await self.token_pool.acquire()
    self.debugger.log_token_flow("ACQUIRED", token_idx, task.task_id)

    try:
        env = os.environ.copy()
        env["CLAUDE_CODE_TOKEN"] = token

        # Debug: Log subprocess execution
        self.debugger.log_subprocess(cmd, env, cwd=str(agent_work_dir) if hasattr(self, 'agent_work_dir') else None)

        # Execute
        task.start_time = datetime.now().timestamp()
        task.status = "running"

        self.debugger.log_variable("task.status", "running")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            cwd=str(agent_work_dir) if self.enable_dynamic_configs else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Debug: Log process ID
        self.debugger.log_variable("process.pid", process.pid)

        stdout, stderr = await process.communicate()

        task.end_time = datetime.now().timestamp()
        duration = task.end_time - task.start_time

        # Debug: Log execution results
        self.debugger.log_variable("returncode", process.returncode)
        self.debugger.log_variable("duration", f"{duration:.2f}s")

        if process.returncode == 0:
            task.status = "completed"
            task.result = json.loads(stdout.decode())

            # Debug: Log success
            self.debugger.log_variable("task.status", "completed")
            if self.debug_level >= 3:
                self.debugger.log_variable("stdout_length", len(stdout))
                self.debugger.log_variable("result_keys", list(task.result.keys()) if isinstance(task.result, dict) else "non-dict")

        else:
            task.status = "failed"
            task.error = stderr.decode()

            # Debug: Log failure details
            self.debugger.log_variable("task.status", "failed")
            self.debugger.log_variable("stderr", task.error[:500] if len(task.error) > 500 else task.error)

    except Exception as e:
        # Debug: Log exception
        self.debugger.log_error(e, f"execute_agent({task.task_id})")
        task.status = "failed"
        task.error = str(e)

    finally:
        # Always release token with debug logging
        if hasattr(self.token_pool, 'release'):
            self.token_pool.release(token_idx)
            self.debugger.log_token_flow("RELEASED", token_idx, task.task_id)

    # Debug: Log task completion
    self.debugger.log_exit("execute_agent", {"status": task.status, "duration": duration if 'duration' in locals() else None})

    return task.to_dict()
```

### 6. Agent Debug Flag Integration

**Modify command building section**:

```python
# Build command with agent-specific debug settings
cmd = self.claude_cmd.copy()

# Agent debug mode configuration
if self.agent_debug_mode:
    # Add debug flag
    cmd.append("--debug")

    # Add verbose output if debug level is high
    if self.debug_level >= 2:
        cmd.append("--verbose")

    # Add trace mode for maximum verbosity
    if self.debug_level >= 3:
        cmd.append("--trace")
        cmd.extend(["--log-level", "TRACE"])
```

### 7. Debug Output Formatting

#### Standard Debug Output Format
```
[2025-09-07 10:23:45] [DEBUG] [execute_agent:282] ENTRY: execute_agent(task_id=research_001, task_type=research, session_id=abc123)
[2025-09-07 10:23:45] [DEBUG] [execute_agent:285] VAR: task.prompt = Research async patterns in Python
[2025-09-07 10:23:45] [DEBUG] [execute_agent:320] TOKEN: ACQUIRED token[0] for research_001
[2025-09-07 10:23:45] [DEBUG] [execute_agent:335] EXEC: claude -p --model opus --mcp-config ./mcp.json -- Research async patterns
[2025-09-07 10:23:45] [DEBUG] [execute_agent:336]   CWD: /output/agent_workspaces/research_001
[2025-09-07 10:23:50] [DEBUG] [execute_agent:355] VAR: returncode = 0
[2025-09-07 10:23:50] [DEBUG] [execute_agent:356] VAR: duration = 5.23s
[2025-09-07 10:23:50] [DEBUG] [execute_agent:375] TOKEN: RELEASED token[0] for research_001
[2025-09-07 10:23:50] [DEBUG] [execute_agent:380] EXIT: execute_agent -> {'status': 'completed', 'duration': 5.23}
```

#### Error Debug Output Format
```
[2025-09-07 10:23:45] [ERROR] [execute_agent:365] ERROR in execute_agent(task_001): RuntimeError: Command failed
[2025-09-07 10:23:45] [ERROR] [execute_agent:366] TRACE:
Traceback (most recent call last):
  File "generic_orchestrator.py", line 350, in execute_agent
    process = await asyncio.create_subprocess_exec(...)
RuntimeError: Command failed
```

### 8. Debug Statistics Collection

**Add to GenericOrchestrator class**:

```python
def _init_debug_stats(self):
    """Initialize debug statistics collection"""
    self.debug_stats = {
        "token_acquisitions": 0,
        "token_releases": 0,
        "subprocess_calls": 0,
        "errors": [],
        "task_durations": [],
        "memory_usage": [],
    }

def _update_debug_stats(self, stat_type: str, value: Any = None):
    """Update debug statistics"""
    if self.debug_level == 0:
        return

    if stat_type == "token_acquire":
        self.debug_stats["token_acquisitions"] += 1
    elif stat_type == "token_release":
        self.debug_stats["token_releases"] += 1
    elif stat_type == "subprocess":
        self.debug_stats["subprocess_calls"] += 1
    elif stat_type == "error":
        self.debug_stats["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": str(value)
        })
    elif stat_type == "duration":
        self.debug_stats["task_durations"].append(value)

def get_debug_report(self) -> Dict:
    """Generate debug statistics report"""
    if self.debug_level == 0:
        return {"debug": "disabled"}

    return {
        "debug_level": self.debug_level,
        "statistics": self.debug_stats,
        "token_balance": self.debug_stats["token_acquisitions"] - self.debug_stats["token_releases"],
        "avg_duration": sum(self.debug_stats["task_durations"]) / len(self.debug_stats["task_durations"]) if self.debug_stats["task_durations"] else 0,
        "error_count": len(self.debug_stats["errors"])
    }
```

### 9. Environment Variable Debug Support

```python
# Check for debug environment variables
DEBUG_ENV_VARS = {
    "ORCHESTRATOR_DEBUG": "debug_level",
    "ORCHESTRATOR_DEBUG_FILE": "debug_log_file",
    "AGENT_DEBUG": "agent_debug_mode",
    "ORCHESTRATOR_TRACE": "enable_trace",
}

for env_var, param in DEBUG_ENV_VARS.items():
    if env_var in os.environ:
        value = os.environ[env_var]
        if param == "debug_level":
            self.debug_level = int(value)
        elif param == "agent_debug_mode":
            self.agent_debug_mode = value.lower() in ("true", "1", "yes")
        elif param == "debug_log_file":
            self.debug_log_file = Path(value)
```

## Testing Requirements

### Unit Tests for Debug Features

```python
def test_debug_logging_basic():
    """Test basic debug logging functionality"""
    orchestrator = GenericOrchestrator(
        output_dir=Path("/tmp/test"),
        debug_level=1
    )
    # Verify debug file created
    # Verify basic logging works

def test_debug_logging_verbose():
    """Test verbose debug logging"""
    # Test variable logging
    # Test subprocess logging

def test_debug_logging_trace():
    """Test trace-level debug logging"""
    # Test token logging
    # Test environment logging

def test_debug_statistics():
    """Test debug statistics collection"""
    # Verify stats are collected
    # Test report generation
```

## Performance Impact

| Debug Level | Performance Impact | Use Case |
|-------------|-------------------|----------|
| 0 (OFF) | None | Production |
| 1 (BASIC) | ~2% overhead | Development |
| 2 (VERBOSE) | ~5% overhead | Debugging |
| 3 (TRACE) | ~10% overhead | Deep debugging |

## Security Considerations

1. **Token Masking**: Tokens are NEVER logged at levels < 3
2. **API Key Masking**: All API keys are masked in logs
3. **Password Masking**: Passwords are always redacted
4. **Sensitive Data**: Use `sensitive=True` parameter for logging

## Debug Commands

### Enable Debug via Environment
```bash
export ORCHESTRATOR_DEBUG=2
export AGENT_DEBUG=true
python orchestrator.py
```

### Enable Debug Programmatically
```python
orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    tokens=token_list,
    debug_level=2,
    agent_debug_mode=True,
    debug_log_file=Path("./debug.log")
)
```

### View Debug Report
```python
# After execution
report = orchestrator.get_debug_report()
print(json.dumps(report, indent=2))
```

## Implementation Checklist

- [ ] Add OrchestratorDebugger class
- [ ] Add debug_trace decorator
- [ ] Integrate debug logging in __init__
- [ ] Add debug logging to execute_agent
- [ ] Implement token flow logging
- [ ] Add subprocess command logging
- [ ] Implement error detail logging
- [ ] Add debug statistics collection
- [ ] Create debug report generation
- [ ] Add agent debug flag support
- [ ] Implement sensitive data masking
- [ ] Add environment variable support
- [ ] Create unit tests
- [ ] Document performance impact
- [ ] Add debug examples to README
