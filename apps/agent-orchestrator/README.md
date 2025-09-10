# Agent Orchestrator

**The Core Execution Engine for Multi-Agent Coordination**

## Overview

Agent Orchestrator is a production-ready system for coordinating multiple AI agents to execute complex tasks in parallel. It serves as the foundation for the entire ecosystem, enabling sophisticated workflows through intelligent task distribution and dependency management.

## Key Features

- **Multi-Agent Coordination**: Execute up to 15+ agents in parallel with intelligent resource management
- **Token Pool Management**: Robust token loading with 4-strategy fallback system
- **Dependency Resolution**: Automatic dependency tracking and execution ordering
- **State Persistence**: Checkpoint system for recovery and resumption
- **Quality Gates**: Built-in validation and quality assurance
- **Advanced Monitoring**: Real-time performance tracking and alerting
- **Background Execution**: Long-running task support with status monitoring

## Architecture

```
agent-orchestrator/
├── src/
│   ├── generic_orchestrator.py     # Core orchestration engine
│   ├── token_loader.py             # Multi-strategy token management
│   └── unified/                    # Advanced orchestration features
│       ├── unified_orchestrator.py # Enhanced capabilities
│       └── modules/                # Modular components
├── apps_audit_tasks.json          # Audit workflow definitions
├── system_analysis_tasks.json     # System analysis workflows
└── outputs/                        # Execution results and logs
```

## Quick Start

### Basic Usage
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
python run_apps_audit.py           # Run comprehensive ecosystem audit
python run_system_analysis.py      # Analyze system architecture
```

### Advanced Usage with Python
```python
from src.generic_orchestrator import AgentTask, GenericOrchestrator

# Create tasks
tasks = [
    AgentTask(
        task_id="analyze_code",
        task_type="code-analyzer",
        prompt="Analyze the codebase for patterns and quality"
    )
]

# Execute with orchestrator
orchestrator = GenericOrchestrator(max_parallel=10)
results = await orchestrator.execute_batch(tasks)
```

## Integration Points

- **WBS Documenter**: Uses orchestrator for parallel documentation generation
- **Autonomous Coder**: Integrates for self-coding capabilities
- **Multi-Agent Monitor**: Provides safety layer for orchestrator operations
- **OpsVI Monitoring**: Consolidated observability for all orchestrator activities

## Recent Achievements

- ✅ **100% Success Rate**: 15-agent audit completed flawlessly
- ✅ **Token Loading Fixed**: Robust 4-strategy loading system implemented
- ✅ **State Persistence**: Checkpoint and resume capabilities active
- ✅ **Quality Gates**: Comprehensive validation pipeline operational

## Configuration

The orchestrator automatically loads tokens using multiple strategies:
1. Relative import (when called from orchestrator directory)
2. Absolute import (when called from other apps)
3. Environment variable fallback
4. Configuration file loading

## Docker Deployment

```yaml
version: '3.8'
services:
  agent-orchestrator:
    build: .
    environment:
      - MAX_PARALLEL=15
      - TOKEN_POOL_SIZE=20
    volumes:
      - ./outputs:/app/outputs
```

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Integration test with live agents
python test_orchestrator_integration.py

# Performance benchmarks
python benchmark_orchestrator.py
```

## Performance Metrics

- **Parallel Execution**: 15 agents simultaneously
- **Task Completion**: 100% success rate in production
- **Resource Usage**: Optimized for <400MB RAM target
- **API Costs**: <$2.00 per task execution

## Production Status

**🟢 PRODUCTION READY** - Currently serving as the foundation for:
- Apps ecosystem audit (100% success)
- System analysis workflows
- Cross-app integration projects
- Documentation generation pipelines

## Contributing

This is the core execution engine. Changes should be thoroughly tested and approved as they impact the entire ecosystem.

## Support

For issues or questions about agent orchestrator functionality, check:
- `outputs/logs/` for execution logs
- `outputs/checkpoints/` for state information
- Background processes with `BashOutput` tool
