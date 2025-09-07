# Agent Orchestrator Documentation

## Quick Links

- 🚀 [Quick Start](../QUICKSTART.md) - Get started in 30 seconds
- 📚 [Tutorials](TUTORIALS.md) - Step-by-step guides
- 📖 [API Reference](API_REFERENCE.md) - Complete API documentation
- 🏗️ [Architecture](ARCHITECTURE.md) - System design and internals
- 🔧 [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- ✅ [Test Results](FIXED.md) - Validation and fixes applied

## Documentation Overview

### For Users

Start with the **[Tutorials](TUTORIALS.md)** to learn how to:
- Create your first orchestration
- Use parallel execution
- Manage dependencies
- Handle errors gracefully
- Build complex pipelines

### For Developers

Review the **[API Reference](API_REFERENCE.md)** for:
- Complete class documentation
- Method signatures and parameters
- Code examples
- Extension points

### For System Administrators

Check the **[Architecture](ARCHITECTURE.md)** for:
- System design
- Performance characteristics
- Scalability limits
- Security considerations

### For Debugging

Use the **[Troubleshooting](TROUBLESHOOTING.md)** guide for:
- Common error messages
- Diagnostic procedures
- Performance optimization
- Debug techniques

## Key Concepts

### 1. Tasks
The basic unit of work. Each task has:
- Unique ID
- Type (research, code, test, etc.)
- Prompt for Claude
- Optional dependencies
- Status tracking

### 2. Dependencies
Tasks can depend on other tasks:
- Sequential execution: A → B → C
- Parallel execution: A → [B, C, D] → E
- Complex graphs supported

### 3. Parallelism
Multiple tasks run simultaneously:
- Limited by token count
- Controlled by max_parallel setting
- Automatic scheduling

### 4. Token Pool
Manages Claude API tokens:
- Round-robin allocation
- Supports multiple tokens
- Thread-safe

### 5. Hooks
Extension points for customization:
- Pre-execution processing
- Prompt building
- Post-execution handling

## Example Orchestration

```python
from generic_orchestrator import GenericOrchestrator, AgentTask
import asyncio

async def example():
    # Create orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"),
        max_parallel=5
    )

    # Define tasks with dependencies
    tasks = [
        AgentTask(
            task_id="research",
            task_type="research",
            prompt="Research Python async patterns"
        ),
        AgentTask(
            task_id="implement",
            task_type="code",
            prompt="Implement an async web server",
            dependencies=["research"]
        )
    ]

    # Execute
    await orchestrator.execute_batch(tasks)

asyncio.run(example())
```

## Performance Expectations

| Tasks | Sequential Time | Parallel Time (5 tokens) | Speedup |
|-------|----------------|--------------------------|---------|
| 10    | 10-20 min      | 2-4 min                  | 5x      |
| 50    | 50-100 min     | 10-20 min                | 5x      |
| 100   | 100-200 min    | 20-40 min                | 5x      |

*Note: Actual times depend on task complexity and Claude model used.*

## Best Practices

1. **Start Small**: Test with 2-3 tasks before scaling
2. **Use Dependencies Wisely**: Minimize sequential chains
3. **Monitor Resources**: Watch memory and disk usage
4. **Handle Errors**: Implement retry logic for critical tasks
5. **Optimize Prompts**: Keep prompts focused and clear

## Support

- **Issues**: Report bugs in [ISSUES.md](../ISSUES.md)
- **Examples**: Check the [examples/](../examples/) directory
- **Source**: Review [generic_orchestrator.py](../src/generic_orchestrator.py)

## Version History

- **v1.0.0** - Initial release with core orchestration features
- **v1.0.1** - Fixed session ID format and command construction
- **v1.0.2** - Added comprehensive documentation

## License

MIT License - See [LICENSE](../LICENSE) for details.
