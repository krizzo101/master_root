# Agent Orchestrator User Guide

**A comprehensive guide to using the Agent Orchestrator system for multi-agent coordination and task automation.**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Features](#core-features)
3. [Common Tasks](#common-tasks)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)
7. [FAQ](#faq)
8. [Advanced Usage](#advanced-usage)

---

## Getting Started

### What is Agent Orchestrator?

Agent Orchestrator is a production-ready system designed to coordinate multiple AI agents to execute complex tasks in parallel. Think of it as a command center that intelligently distributes work across multiple AI assistants, manages dependencies between tasks, and ensures reliable execution with built-in recovery capabilities.

### Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher installed
- Access to Claude API tokens (for agent execution)
- Basic familiarity with command-line interfaces
- Understanding of your project structure

### Quick Installation

1. **Navigate to the orchestrator directory:**
   ```bash
   cd /home/opsvi/master_root/apps/agent-orchestrator
   ```

2. **Verify the installation:**
   ```bash
   python main.py --help
   ```

### Your First Orchestration

Let's start with a simple example to get familiar with the system:

```bash
# Run the built-in example tasks
python main.py --example --max-parallel 3

# Or run a comprehensive system analysis
python run_system_analysis.py --target /path/to/your/project
```

**What happens:** The orchestrator will create multiple AI agents that work together to analyze your system, each focusing on different aspects like architecture, code quality, and documentation.

---

## Core Features

### 🎯 Multi-Agent Coordination
Execute up to 15 agents simultaneously, each working on different parts of your task while the orchestrator manages coordination and prevents conflicts.

### 🔄 Smart Dependency Management
Define task dependencies and let the orchestrator automatically determine the optimal execution order. For example, "analyze code" can run before "write documentation" which depends on the analysis results.

### 💾 Checkpoint & Recovery
Never lose work again. The system automatically creates checkpoints and can resume from any point if execution is interrupted.

### 📊 Real-time Monitoring
Track progress with built-in dashboard integration, real-time status updates, and detailed execution logs.

### 🔧 Quality Gates
Built-in validation ensures tasks meet quality standards before proceeding to dependent tasks.

### 🚀 Background Execution
Long-running tasks continue in the background while you work on other things.

---

## Common Tasks

### Task 1: Generate Complete Documentation for Your Project

**Use Case:** You have a software project and want comprehensive documentation generated automatically.

```bash
# Generate complete documentation suite
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-awesome-app" \
  --app-root "/path/to/my/project" \
  --template comprehensive
```

**What you get:**
- `README.md` - Project overview and quick start
- `ARCHITECTURE.md` - System design and components
- `API_REFERENCE.md` - Complete API documentation
- `USER_GUIDE.md` - End-user documentation
- `DEVELOPER_GUIDE.md` - Development setup and workflows
- `DEPLOYMENT.md` - Deployment and operations guide

### Task 2: Analyze System Architecture

**Use Case:** Understand the structure and health of an existing codebase.

```bash
# Run comprehensive system analysis
python run_system_analysis.py --target "/path/to/analyze"
```

**What you get:**
- Code quality assessment
- Architecture analysis
- Dependency mapping
- Security audit
- Performance recommendations

### Task 3: Custom Multi-Step Workflow

**Use Case:** You have a complex workflow that needs multiple specialized agents.

1. **Create a task definition file (`my_workflow.json`):**
   ```json
   {
     "tasks": [
       {
         "task_id": "research_phase",
         "task_type": "research",
         "prompt": "Research best practices for Python web development"
       },
       {
         "task_id": "design_phase",
         "task_type": "design",
         "prompt": "Design an API based on the research findings",
         "dependencies": ["research_phase"]
       },
       {
         "task_id": "implementation",
         "task_type": "code",
         "prompt": "Implement the API design",
         "dependencies": ["design_phase"]
       }
     ]
   }
   ```

2. **Execute the workflow:**
   ```bash
   python main.py --tasks-file my_workflow.json --max-parallel 5
   ```

### Task 4: Resume Interrupted Work

**Use Case:** Your workflow was interrupted and you want to continue where you left off.

```bash
# List available checkpoints
python run_orchestrator_task.py --list-checkpoints --app-name "my-project"

# Resume from a specific checkpoint
python run_orchestrator_task.py --resume-checkpoint checkpoint_id_here
```

---

## Configuration

### Basic Configuration

The orchestrator uses intelligent defaults but can be customized:

**Maximum Parallel Agents:**
```bash
python main.py --max-parallel 10  # Run up to 10 agents simultaneously
```

**Output Directory:**
```bash
python main.py --output-dir "/custom/output/path"
```

**Enable Dashboard Integration:**
```bash
python main.py --enable-dashboard
```

### Token Management

The system automatically manages Claude API tokens with multiple fallback strategies:

1. **Automatic Token Loading** - Tries multiple token loading methods
2. **Token Pool Management** - Distributes requests across available tokens
3. **Rate Limit Handling** - Automatically manages API rate limits
4. **Fallback Systems** - Switches to alternative providers if needed

### Configuration Files

**Production Settings (`production_config.json`):**
```json
{
  "host": "0.0.0.0",
  "port": 8765,
  "max_connections": 500,
  "max_parallel": 15,
  "enable_monitoring": true
}
```

**Logging Configuration (`logging_config.json`):**
- Centralized logging setup
- Different log levels for development vs. production
- Automatic log rotation and cleanup

---

## Troubleshooting

### Common Issues and Solutions

#### ❌ "No tokens available" Error
**Problem:** The orchestrator can't find Claude API tokens.
**Solution:**
1. Verify your tokens are properly configured
2. Check the token loading logs for specific errors
3. Ensure tokens have sufficient quota remaining

```bash
# Check token status
python -c "from src.token_loader import load_tokens; print(f'Loaded {len(load_tokens())} tokens')"
```

#### ❌ "Task failed with dependency error"
**Problem:** A task is waiting for a dependency that failed.
**Solution:**
1. Check the logs for the specific failure reason
2. Resume from the last successful checkpoint
3. Review task dependencies in your JSON file

```bash
# Check detailed logs
tail -f outputs/logs/orchestrator_*.log
```

#### ❌ "Max parallel limit reached"
**Problem:** Too many agents trying to run simultaneously.
**Solution:**
1. Reduce the `--max-parallel` setting
2. Check system resources (RAM, CPU)
3. Review task definitions for unnecessary parallelism

#### ❌ "Dashboard not updating"
**Problem:** Real-time updates aren't showing in the dashboard.
**Solution:**
1. Ensure `--enable-dashboard` flag is used
2. Check network connectivity on the dashboard port
3. Review browser console for WebSocket connection errors

### Getting Help

1. **Check the logs first:** Most issues have detailed information in the log files
2. **Use verbose mode:** Add `--verbose` or `--debug` flags for more detailed output
3. **Review checkpoints:** Use `--list-checkpoints` to see execution history

---

## Best Practices

### 🎯 Task Design

**DO:**
- Keep individual task prompts focused and specific
- Use clear, descriptive task IDs
- Define dependencies explicitly
- Include context information in task definitions

**DON'T:**
- Create overly broad tasks that try to do everything
- Skip dependency definitions when tasks rely on each other
- Use vague prompts that could be interpreted multiple ways

### 🔄 Workflow Organization

**Start Small:**
Begin with 2-3 tasks to understand the orchestrator behavior before scaling to complex workflows.

**Use Templates:**
Leverage built-in templates like `system-documentation` before creating custom workflows.

**Plan Dependencies:**
Map out your workflow dependencies before creating the JSON file:
```
Research → Analysis → Design → Implementation → Testing
```

### 💾 Resource Management

**Optimal Parallel Settings:**
- For documentation: 3-5 parallel agents
- For analysis: 5-8 parallel agents
- For complex workflows: 8-12 parallel agents
- Never exceed 15 without careful resource monitoring

**Checkpoint Strategy:**
- Enable checkpointing for any workflow longer than 30 minutes
- Use checkpoint interval of 3-5 tasks for most workflows
- Keep workspaces for important workflows until completion confirmed

### 📊 Monitoring and Maintenance

**Regular Monitoring:**
```bash
# Monitor active processes
python agent_background_monitor.py

# Check system health
python production_dashboard.py
```

**Log Management:**
- Regularly review logs for performance patterns
- Archive old logs to prevent disk space issues
- Monitor token usage to avoid quota exhaustion

---

## FAQ

### Q: How many agents can I run simultaneously?
**A:** The orchestrator supports up to 15 parallel agents, but the optimal number depends on your system resources and task complexity. Start with 5-8 agents and adjust based on performance.

### Q: What happens if my internet connection is interrupted?
**A:** The orchestrator automatically creates checkpoints every few completed tasks. You can resume from the last checkpoint using the `--resume-checkpoint` command.

### Q: Can I modify tasks while they're running?
**A:** No, running tasks cannot be modified. However, you can add new tasks to the queue or create follow-up workflows based on intermediate results.

### Q: How much does it cost to run the orchestrator?
**A:** API costs vary based on task complexity. Typical documentation workflows cost $1-3. Analysis workflows cost $2-5. The orchestrator optimizes token usage to minimize costs.

### Q: Can I run multiple orchestrations simultaneously?
**A:** Yes, but each should use different output directories to avoid conflicts. Monitor system resources when running multiple orchestrations.

### Q: What's the difference between main.py and run_orchestrator_task.py?
**A:**
- `main.py` is for custom task definitions and JSON workflows
- `run_orchestrator_task.py` is for built-in workflows like system documentation

### Q: How do I know if my tasks are high quality?
**A:** The orchestrator includes built-in quality gates that validate outputs. Enable them with the `--use-enhanced` flag for additional quality assurance.

### Q: Can I integrate with other tools?
**A:** Yes, the orchestrator supports MCP (Model Context Protocol) integrations and can work with various external tools and APIs.

---

## Advanced Usage

### Custom Agent Types

Create specialized agents for specific domains:

```python
from src.generic_orchestrator import AgentTask

# Create a specialized security audit task
security_task = AgentTask(
    task_id="security_audit",
    task_type="security-expert",
    prompt="Perform comprehensive security audit focusing on authentication and data protection",
    quality_gates=["security_checklist", "vulnerability_scan"]
)
```

### Enhanced Orchestrator Features

Enable advanced capabilities for production workflows:

```bash
python main.py \
  --use-enhanced \
  --enable-dashboard \
  --tasks-file complex_workflow.json \
  --max-parallel 10
```

**Enhanced features include:**
- Advanced quality gates and validation
- Real-time performance monitoring
- Automatic optimization recommendations
- Integration with external monitoring systems

### Integration with External Systems

**Dashboard Integration:**
```python
# Custom dashboard callback
def dashboard_callback(state_data):
    # Send updates to your dashboard
    webhook_url = "https://your-dashboard.com/api/updates"
    requests.post(webhook_url, json=state_data)

orchestrator = GenericOrchestrator(
    dashboard_state_callback=dashboard_callback
)
```

**MCP Tool Integration:**
The orchestrator can use MCP tools for specialized capabilities:
- Web scraping and research
- File system operations
- Database interactions
- External API integrations

### Performance Optimization

**Token Efficiency:**
- Use specific, focused prompts to minimize token usage
- Enable context sharing between related tasks
- Leverage built-in optimization features

**Resource Optimization:**
- Monitor memory usage with background monitor
- Adjust parallel limits based on system performance
- Use checkpoint intervals appropriate for your workflow length

**Cost Management:**
- Track API costs using built-in metrics
- Use test runs with smaller agent counts before full execution
- Leverage token pools effectively across multiple workflows

---

## Support and Updates

### Getting Help
- Check logs first: `outputs/logs/orchestrator_*.log`
- Use debug mode: `--debug` for detailed troubleshooting
- Review checkpoint status: `--list-checkpoints`

### Best Resources
- **Documentation:** `/docs/` directory for technical references
- **Examples:** Built-in examples via `--example` flag
- **Templates:** Pre-built workflows for common use cases

### System Requirements
- **Minimum:** Python 3.8, 4GB RAM, Claude API access
- **Recommended:** Python 3.10+, 8GB RAM, multiple API tokens
- **Optimal:** 16GB RAM for large-scale orchestrations

---

*This guide covers the essential usage patterns for Agent Orchestrator. For technical implementation details, see the [Developer Guide](DEVELOPER_GUIDE.md) and [Architecture Documentation](ARCHITECTURE.md).*
