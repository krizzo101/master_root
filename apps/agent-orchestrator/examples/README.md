# Agent Orchestrator Examples

A comprehensive collection of examples demonstrating the Agent Orchestrator framework capabilities, organized by complexity and use case.

## 📁 Directory Structure

```
examples/
├── basic/          # Simple, beginner-friendly examples
├── advanced/       # Complex features and patterns
├── integration/    # Full system integration examples
└── archive/        # Deprecated or legacy examples
```

## 🎯 Quick Start

New to Agent Orchestrator? Start with these examples in order:

1. **[basic/hello_world_async.py](basic/hello_world_async.py)** - Simplest async function demonstration
2. **[basic/simple_example.py](basic/simple_example.py)** - Basic orchestrator usage
3. **[basic/simple_async_example.py](basic/simple_async_example.py)** - Async queue and task patterns
4. **[integration/practical_orchestrator_example.py](integration/practical_orchestrator_example.py)** - Real-world orchestration

## 📚 Examples by Category

### Basic Examples
*Perfect for beginners and understanding core concepts*

| File | Description | Key Concepts |
|------|-------------|--------------|
| [hello_world_async.py](basic/hello_world_async.py) | Simplest async example | `async/await`, concurrent tasks |
| [simple_example.py](basic/simple_example.py) | Basic orchestrator setup | Core orchestration patterns |
| [simple_async_example.py](basic/simple_async_example.py) | Async system usage | AsyncQueue, AsyncTask, SimpleAsyncExecutor |
| [async_example.py](basic/async_example.py) | Extended async patterns | Error handling, timeouts |
| [monitoring_example.py](basic/monitoring_example.py) | Basic monitoring setup | Progress tracking, event monitoring |
| [test_demo_framework.py](basic/test_demo_framework.py) | Testing framework demo | Unit testing patterns |

### Advanced Examples
*Complex features, patterns, and optimizations*

| File | Description | Key Concepts |
|------|-------------|--------------|
| [agent_collaboration_example.py](advanced/agent_collaboration_example.py) | Multi-agent collaboration | Agent teams, message passing |
| [agent_team_manager_examples.py](advanced/agent_team_manager_examples.py) | Team management patterns | Dynamic teams, role assignment |
| [collaborative_orchestrator_example.py](advanced/collaborative_orchestrator_example.py) | Advanced orchestration | Complex workflows, dependencies |
| [enhanced_example.py](advanced/enhanced_example.py) | Enhanced features demo | Advanced configuration, optimization |
| [escalation_demo.py](advanced/escalation_demo.py) | Error escalation patterns | Hierarchical error handling |
| [escalation_benchmarks.py](advanced/escalation_benchmarks.py) | Performance benchmarking | Metrics, profiling |
| [escalation_validator.py](advanced/escalation_validator.py) | Validation patterns | Quality gates, validation chains |
| [self_improvement_demo.py](advanced/self_improvement_demo.py) | Self-improving systems | Adaptive behavior, learning |

### Integration Examples
*Full system integration and real-world scenarios*

| File | Description | Key Concepts |
|------|-------------|--------------|
| [practical_orchestrator_example.py](integration/practical_orchestrator_example.py) | Production-ready orchestration | 10-parallel execution, monitoring |
| [collaboration_demo.py](integration/collaboration_demo.py) | Complete collaboration system | Full agent ecosystem |
| [event_system_demo.py](integration/event_system_demo.py) | Event-driven architecture | Event bus, pub/sub patterns |
| [message_bus_demo.py](integration/message_bus_demo.py) | Message bus integration | Async messaging, routing |
| [web_api_demo.py](integration/web_api_demo.py) | REST API integration | HTTP endpoints, async handlers |
| [quality_gate_examples.py](integration/quality_gate_examples.py) | Quality assurance gates | Validation pipelines |
| [validation_examples.py](integration/validation_examples.py) | Comprehensive validation | Multi-stage validation |
| [run_execution_plan_examples.py](integration/run_execution_plan_examples.py) | Execution plan workflows | Plan-based orchestration |
| [run_complete_validation.py](integration/run_complete_validation.py) | Full system validation | End-to-end testing |

#### Execution Plans (JSON)
*Pre-defined execution plans for common scenarios*

- **[simple_execution_plan.json](integration/simple_execution_plan.json)** - Basic linear execution
- **[sdlc_execution_plan.json](integration/sdlc_execution_plan.json)** - Software development lifecycle workflow
- **[self_improvement_execution_plan.json](integration/self_improvement_execution_plan.json)** - Adaptive improvement cycles

## 🚀 Running Examples

### Prerequisites

```bash
# Ensure you're in the project root
cd /path/to/agent-orchestrator

# Install dependencies
pip install -r requirements.txt
```

### Running Basic Examples

```bash
# Run the hello world example
python examples/basic/hello_world_async.py

# Run simple async example
python examples/basic/simple_async_example.py
```

### Running Advanced Examples

```bash
# Agent collaboration
python examples/advanced/agent_collaboration_example.py

# Escalation demo with metrics
python examples/advanced/escalation_demo.py --metrics
```

### Running Integration Examples

```bash
# Practical orchestrator with 10 parallel agents
python examples/integration/practical_orchestrator_example.py

# Web API server
python examples/integration/web_api_demo.py --port 8080

# Full validation suite
python examples/integration/run_complete_validation.py
```

## 💡 Common Patterns

### 1. Basic Async Pattern
```python
import asyncio
from src.simple_async_system import SimpleAsyncExecutor

async def main():
    executor = SimpleAsyncExecutor(max_concurrent=3)
    tasks = [task1(), task2(), task3()]
    results = await executor.execute_batch(tasks)
```

### 2. Orchestrator with Monitoring
```python
from src.practical_orchestrator import PracticalOrchestrator

orchestrator = PracticalOrchestrator(
    max_parallel=10,
    enable_monitoring=True
)
orchestrator.set_progress_callback(lambda e, d: print(f"{e}: {d}"))
```

### 3. Agent Collaboration
```python
from src.collaboration import AgentTeam

team = AgentTeam()
team.add_agent("analyzer", AnalyzerAgent())
team.add_agent("processor", ProcessorAgent())
result = await team.collaborate(task)
```

## 📊 Performance Benchmarks

Run the benchmark suite to test performance:

```bash
# Run escalation benchmarks
python examples/advanced/escalation_benchmarks.py

# Results will be saved to:
# - benchmarks/results/performance_metrics.json
# - benchmarks/reports/benchmark_report.md
```

## 🧪 Testing Examples

Most examples include self-contained tests. To run all example tests:

```bash
# Run test framework demo
python examples/basic/test_demo_framework.py

# Test web server functionality
python examples/integration/test_web_server.py
```

## 📝 Best Practices

1. **Start Simple**: Begin with basic examples before moving to advanced
2. **Check Dependencies**: Ensure all required modules are installed
3. **Monitor Resources**: Use monitoring examples to track performance
4. **Error Handling**: Study escalation examples for robust error management
5. **Parallel Execution**: See practical_orchestrator_example.py for optimal parallelism

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root
2. **Async Errors**: Python 3.7+ required for async features
3. **Port Conflicts**: Web API examples default to port 8080
4. **Memory Issues**: Limit parallel execution for resource-constrained systems

### Getting Help

- Check individual example docstrings for detailed usage
- Review integration tests in `/tests` directory
- See main project README for framework documentation

## 🚧 Archived Examples

Legacy or deprecated examples are kept in `archive/` for reference but may not work with current versions.

## 📈 Example Complexity Guide

- ⭐ **Basic**: < 100 lines, single concept
- ⭐⭐ **Intermediate**: 100-300 lines, multiple concepts
- ⭐⭐⭐ **Advanced**: 300+ lines, complex patterns
- ⭐⭐⭐⭐ **Integration**: Full system examples

## 🤝 Contributing

To add new examples:

1. Choose appropriate category (basic/advanced/integration)
2. Follow naming convention: `feature_example.py`
3. Include comprehensive docstrings
4. Add entry to this README
5. Test thoroughly before committing

---

*Last updated: September 2024*
*Examples tested with: Python 3.9+, Agent Orchestrator v2.0*