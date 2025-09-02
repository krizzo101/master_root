# Quick Start Guide

## 1. Setup (30 seconds)

```bash
make setup
```

## 2. Run Example

```bash
# Interactive menu
./run.py

# Or directly
make run
```

## 3. Use the Framework

```python
from src.generic_orchestrator import GenericOrchestrator, AgentTask
import asyncio

async def main():
    # Create orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"),
        max_parallel=10
    )

    # Define tasks
    tasks = [
        AgentTask(
            task_id="task1",
            task_type="research",
            prompt="Research something"
        ),
        AgentTask(
            task_id="task2",
            task_type="implement",
            prompt="Build something",
            dependencies=["task1"]  # Runs after task1
        )
    ]

    # Run
    await orchestrator.execute_batch(tasks)

asyncio.run(main())
```

## 4. Monitor Progress

In separate terminals:
```bash
# Watch file system
./scripts/filesystem_monitor.sh

# Watch processes
./scripts/claude_process_monitor.sh
```

## 5. View Results

Results are saved to `output/tasks/` as JSON files.

## Common Commands

```bash
make help      # Show all commands
make test      # Run tests
make clean     # Clean output
make status    # Project status
```

## Performance Tips

1. **Use optimizations** (3-5s per agent):
   ```python
   orchestrator = GenericOrchestrator(use_optimizations=True)
   ```

2. **Add more tokens** for parallelism:
   ```python
   tokens = ["token1", "token2", "token3"]
   orchestrator = GenericOrchestrator(tokens=tokens)
   ```

3. **Batch wisely**:
   - 10-20 agents per batch is optimal
   - Use dependencies to control flow

## Next Steps

- Read `docs/ORCHESTRATOR_README.md` for full documentation
- Check `src/wbs_implementation.py` for complex example
- Review test results in `docs/COMPREHENSIVE_TEST_RESULTS.md`
