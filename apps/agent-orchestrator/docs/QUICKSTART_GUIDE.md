# Agent Orchestrator - 5-Minute Quickstart Guide

Get your agent orchestration system running in under 5 minutes with this step-by-step guide.

## 🚀 Prerequisites (30 seconds)

Before starting, ensure you have:

- **Python 3.8+** installed
- **Claude CLI** installed and accessible via command line
- **CLAUDE_CODE_TOKEN** environment variable set
- **Unix-like system** (Linux/macOS/WSL)

Quick verification:
```bash
python3 --version    # Should show 3.8+
claude --version     # Should show Claude CLI version
echo $CLAUDE_CODE_TOKEN  # Should show your token
```

## 📦 Step 1: Installation (1 minute)

Navigate to the agent orchestrator directory and run the setup script:

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
./setup.sh
```

The setup script will:
- ✅ Verify Claude CLI installation
- ✅ Check token configuration
- ✅ Create minimal MCP config
- ✅ Set up output directory

## 🎯 Step 2: Run Your First Example (2 minutes)

Launch the interactive runner:

```bash
python3 run.py
```

Choose **Option 1** (Simple example) for your first run. This will:
- Create 3 sequential tasks (research → design → implement)
- Run them with dependency management
- Save results to `./output/` directory

**Expected output:**
```
Agent Orchestrator Framework
========================================
1. Simple example (3 sequential tasks)
2. Parallel example (5 parallel + 1 summary)
3. Exit

Select option (1-3): 1
```

## 💡 Step 3: Try Parallel Execution (1 minute)

Run the script again and choose **Option 2** to see parallel execution:

```bash
python3 run.py
# Choose option 2
```

This demonstrates:
- 5 research tasks running simultaneously
- 1 summary task that waits for all research to complete
- Efficient token usage with round-robin allocation

## 🔧 Step 4: Your First Custom Script (1 minute)

Create your own orchestration script:

```python
#!/usr/bin/env python3
"""My first orchestrator script"""

import asyncio
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator, AgentTask

async def my_workflow():
    # Create orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./my_output"),
        max_parallel=3,
        use_optimizations=True
    )

    # Define your tasks
    tasks = [
        AgentTask(
            task_id="analyze",
            task_type="analysis",
            prompt="Analyze current market trends in AI"
        ),
        AgentTask(
            task_id="report",
            task_type="documentation",
            prompt="Create a summary report of the analysis",
            dependencies=["analyze"]  # Waits for analyze to complete
        )
    ]

    # Execute
    await orchestrator.execute_batch(tasks)

if __name__ == "__main__":
    asyncio.run(my_workflow())
```

Save as `my_script.py` and run:
```bash
python3 my_script.py
```

## 📊 Understanding Results

Your results are saved in JSON format under `./output/` (or your specified directory):

```json
{
  "task_id": "research",
  "status": "completed",
  "result": {
    "response": "Async programming in Python offers several key benefits...",
    "execution_time": 15.2,
    "success": true
  }
}
```

## 🎪 Advanced Features (Optional)

### Parallel Execution with Dependencies
```python
tasks = [
    AgentTask("start", "init", "Initialize project"),
    AgentTask("task1", "work", "Do work A", ["start"]),
    AgentTask("task2", "work", "Do work B", ["start"]),  # Parallel with task1
    AgentTask("merge", "combine", "Combine results", ["task1", "task2"])
]
```

### Context Passing Between Tasks
```python
task = AgentTask(
    task_id="enhanced_task",
    task_type="analysis",
    prompt="Analyze with context",
    context={
        "previous_results": results_from_other_task,
        "settings": {"depth": "detailed"},
        "shared_data": cached_information
    }
)
```

### Custom Hooks
```python
async def my_preprocessor(task):
    print(f"Starting task: {task.task_id}")
    return task

orchestrator.pre_execute_hook = my_preprocessor
```

## 🛠️ Troubleshooting

### Common Issues

**Token not configured:**
```bash
export CLAUDE_CODE_TOKEN='your-token-here'
```

**Claude CLI not found:**
```bash
# Install Claude CLI first, then retry setup
./setup.sh
```

**Permission errors:**
```bash
chmod +x setup.sh run.py
```

**Import errors:**
```bash
# Ensure you're in the correct directory
cd /home/opsvi/master_root/apps/agent-orchestrator
python3 -c "from src.generic_orchestrator import GenericOrchestrator"
```

## 🎯 What's Next?

Now that you're up and running:

1. **Learn More**: Check out `examples/` directory for advanced patterns
2. **Scale Up**: Try the escalation examples for intelligent agent coordination
3. **Customize**: Explore hooks and custom task types
4. **Monitor**: Use the built-in metrics and dashboard features
5. **Integrate**: Connect with your existing workflows

## 📚 Quick Reference

### Key Files
- `src/generic_orchestrator.py` - Core orchestrator framework
- `run.py` - Interactive examples
- `setup.sh` - Environment setup
- `examples/` - Advanced usage patterns

### Key Classes
- `GenericOrchestrator` - Main orchestration engine
- `AgentTask` - Task definition with dependencies
- `TokenPool` - Token management for parallel execution

### Environment
- `CLAUDE_CODE_TOKEN` - Your Claude API token
- `~/.claude_minimal.json` - MCP configuration file

## ✅ Success Indicators

You've successfully set up the orchestrator when:
- ✅ Setup script completes without errors
- ✅ Simple example runs and generates output files
- ✅ Parallel example shows concurrent execution
- ✅ Custom script executes your defined tasks
- ✅ Results are saved in JSON format

**Total setup time: ~5 minutes**

---

**Need help?** Check the full documentation in `docs/` or run the examples in the `examples/` directory for more advanced use cases.
