# Enhanced Debug Logging for GenericOrchestrator

This implementation provides comprehensive "gory debug logging" for the GenericOrchestrator that captures every value, state change, and decision point during orchestration execution.

## 🎯 What's Included

### Components
- **`debug_logger.py`**: Core logging infrastructure with multi-format output
- **`enhanced_token_pool.py`**: TokenPool with comprehensive logging
- **`enhanced_dependency_manager.py`**: DependencyManager with detailed state tracking
- **`debug_generic_orchestrator.py`**: Full orchestrator with debug logging
- **`log_analyzer.py`**: Analysis utilities for generated logs
- **`test_debug_logging.py`**: Validation tests

### Log Types Generated
1. **Debug Logs** (`.log`): Human-readable detailed execution logs
2. **Values Logs** (`.jsonl`): Machine-readable JSON logs of all state changes
3. **Performance Logs** (`.log`): Timing and performance metrics

## 🚀 Quick Start

### Basic Usage

```python
from pathlib import Path
from src.debug_generic_orchestrator import create_debug_orchestrator, AgentTask

# Create orchestrator with debug logging
orchestrator = create_debug_orchestrator(
    output_dir=Path("./debug_orchestration"),
    max_parallel=5,
    tokens=["your_token_1", "your_token_2", "your_token_3"],
    enable_debug_logging=True
)

# Define tasks
def create_tasks():
    return [
        AgentTask(
            task_id="research_phase",
            task_type="research",
            prompt="Research async programming patterns",
            dependencies=[]
        ),
        AgentTask(
            task_id="analysis_phase", 
            task_type="analysis",
            prompt="Analyze the research findings",
            dependencies=["research_phase"]
        ),
        AgentTask(
            task_id="implementation_phase",
            task_type="implementation",
            prompt="Implement the solution",
            dependencies=["analysis_phase"]
        )
    ]

# Run with full logging
results = await orchestrator.run(create_tasks)
```

### Analyzing Results

```python
from src.log_analyzer import LogAnalyzer

# Analyze generated logs
analyzer = LogAnalyzer(Path("./debug_orchestration/logs"))

# Print summary
analyzer.print_summary()

# Generate comprehensive report
report = analyzer.generate_comprehensive_report(
    Path("./orchestration_analysis.json")
)

# Specific analyses
token_analysis = analyzer.analyze_token_usage()
dependency_analysis = analyzer.analyze_dependency_flow()
performance_analysis = analyzer.analyze_performance_bottlenecks()
```

## 📊 What Gets Logged

### Token Pool Operations
- Every token acquisition with timing
- Token release events
- Pool utilization metrics
- Token distribution patterns
- Peak usage tracking

Example log entry:
```json
{
  "timestamp": "2025-09-07T12:22:05.123456",
  "context": "TokenPool.acquire.post",
  "values": {
    "acquired_token_idx": 0,
    "masked_token": "sk-a***f8b9",
    "tokens_in_use": [0],
    "available_count": 2,
    "total_acquisitions": 1,
    "peak_usage": 1
  }
}
```

### Dependency Management
- Dependency resolution decisions
- State transitions (pending → running → completed/failed)
- Deadlock detection
- Blocking reason analysis

Example log entry:
```json
{
  "timestamp": "2025-09-07T12:22:05.234567",
  "context": "DependencyManager.can_run.decision",
  "values": {
    "task_id": "analysis_phase",
    "can_run": false,
    "unmet_dependencies": ["research_phase"],
    "failed_dependencies": [],
    "dependency_status": {
      "research_phase": {
        "status": "pending",
        "in_completed": false,
        "in_running": false,
        "in_failed": false
      }
    }
  }
}
```

### Task Execution
- Command construction details
- Process execution timing
- Input/output sizes
- Error details and stack traces
- Resource usage

### Performance Metrics
- Operation durations
- Batch execution rounds
- Parallel task counts
- Token acquisition wait times
- Lock contention metrics

## 🔍 Analysis Capabilities

### Token Usage Analysis
```python
token_stats = analyzer.analyze_token_usage()
print(f"Peak concurrent usage: {token_stats['peak_concurrent_usage']}")
print(f"Token distribution: {token_stats['token_distribution']}")
print(f"Most used token: {token_stats['most_used_token_idx']}")
```

### Dependency Flow Analysis
```python
dep_stats = analyzer.analyze_dependency_flow()
print(f"Success rate: {dep_stats['success_rate']:.1f}%")
print(f"Blocking reasons: {dict(dep_stats['blocking_reasons'])}")
print(f"State transitions: {dict(dep_stats['state_transition_flow'])}")
```

### Performance Bottleneck Identification
```python
perf_stats = analyzer.analyze_performance_bottlenecks()
bottlenecks = perf_stats['bottlenecks']['by_total_time']
for operation, stats in bottlenecks[:3]:
    print(f"{operation}: {stats['total_time']:.2f}s total, {stats['avg_time']:.2f}s avg")
```

### Execution Timeline Generation
```python
timeline = analyzer.generate_execution_timeline()
for task_id, analysis in timeline['task_analysis'].items():
    print(f"{task_id}: {analysis['duration_seconds']:.2f}s, {analysis['final_status']}")
```

## 📁 Log File Structure

```
output_dir/
├── logs/
│   ├── debug_GenericOrchestrator_20250907_122205.log          # Main debug log
│   ├── values_GenericOrchestrator_20250907_122205.jsonl       # JSON values log
│   ├── performance_GenericOrchestrator_20250907_122205.log    # Performance metrics
│   ├── debug_TokenPool_20250907_122205.log                    # Token pool debug
│   ├── values_TokenPool_20250907_122205.jsonl                 # Token pool values
│   ├── performance_TokenPool_20250907_122205.log              # Token pool performance
│   ├── debug_DependencyManager_20250907_122205.log            # Dependency debug
│   ├── values_DependencyManager_20250907_122205.jsonl         # Dependency values
│   └── performance_DependencyManager_20250907_122205.log      # Dependency performance
├── tasks/                                                      # Individual task results
├── messages/                                                   # Inter-agent messages
└── agent_workspaces/                                          # Per-agent workspaces (if enabled)
```

## ⚡ Performance Impact

The debug logging is designed to be comprehensive but efficient:

- **Structured logging**: JSON logs for machine processing, text logs for humans
- **Lazy evaluation**: Complex log entries only computed when needed
- **Separate files**: Different log types in separate files to avoid mixing
- **Configurable**: Can be disabled entirely for production use

Typical overhead: ~5-10% performance impact when enabled.

## 🔧 Advanced Configuration

### Custom Log Levels
```python
orchestrator = DebugGenericOrchestrator(
    output_dir=Path("./logs"),
    enable_debug_logging=True,
    # ... other params
)

# Access individual component loggers for custom configuration
orchestrator.debug_logger.logger.setLevel(logging.INFO)  # Less verbose
orchestrator.token_pool.debug_logger.logger.setLevel(logging.DEBUG)  # More verbose
```

### Filtering and Analysis
```python
# Analyze specific task only
timeline = analyzer.generate_execution_timeline(task_filter="research_phase")

# Focus on specific operations
perf_data = analyzer.parse_performance_logs()
agent_operations = [op for op in perf_data if "execute_agent" in op['operation']]
```

### Integration with Original Orchestrator

The debug orchestrator is a drop-in replacement:

```python
# Original
from src.generic_orchestrator import GenericOrchestrator
orchestrator = GenericOrchestrator(...)

# Enhanced with debug logging
from src.debug_generic_orchestrator import create_debug_orchestrator
orchestrator = create_debug_orchestrator(...)

# Same interface, comprehensive logging added
```

## 🎯 Use Cases

### Development & Debugging
- **Issue diagnosis**: Trace exact sequence of events leading to failures
- **Performance optimization**: Identify bottlenecks and inefficiencies  
- **Behavior validation**: Verify orchestrator behaves as expected

### Production Monitoring (Limited)
- **Health monitoring**: Track token usage patterns and dependency resolution
- **Performance tracking**: Monitor execution times and resource utilization
- **Failure analysis**: Detailed error context for post-mortem analysis

### Research & Analysis
- **Pattern discovery**: Analyze orchestration patterns across multiple runs
- **Optimization research**: Data-driven improvements to orchestrator logic
- **Comparative analysis**: Compare different orchestration strategies

## 📋 Example Analysis Output

```
DEBUG ORCHESTRATOR LOG ANALYSIS SUMMARY
============================================================

LOG FILES:
  Debug logs: 3
  Values logs: 3  
  Performance logs: 3
  Total size: 0.5 MB

TOKEN USAGE:
  Total acquisitions: 15
  Total releases: 15
  Peak concurrent usage: 3

PERFORMANCE:
  Total operations measured: 45
  Total measured time: 12.34s
  Top bottleneck: GenericOrchestrator.execute_agent (8.91s)

DEPENDENCY MANAGEMENT:
  Total dependency checks: 28
  Success rate: 78.6%
  State transitions: 15
```

## 🚨 Important Notes

1. **Token Security**: Tokens are masked in logs (e.g., `sk-a***f8b9`) for security
2. **Log Rotation**: Consider log rotation for long-running orchestrations
3. **Storage**: Debug logs can be large - monitor disk usage
4. **Production**: Use with caution in production due to performance overhead
5. **Analysis Time**: Large log files may take time to analyze

## ✅ Validation

Run the test suite to validate the implementation:

```bash
cd /path/to/agent-orchestrator/src
python test_debug_logging.py
```

This validates that all logging components work correctly and produce the expected comprehensive debug output.

---

**The enhanced debug logging provides the "gory details" needed to fully understand and optimize orchestrator behavior at every level, from individual token operations to complete task orchestration flows.**