# Multi-Agent Orchestration System

A comprehensive, production-ready template for building multi-agent orchestration systems with support for complex workflows, agent collaboration, and various execution patterns.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Coordination**: Seamless coordination between specialized agents
- **Workflow Orchestration**: Support for sequential, parallel, conditional, and pipeline execution patterns
- **Inter-Agent Communication**: Robust message-based communication system
- **Real-time Monitoring**: Comprehensive metrics and execution tracking
- **Error Handling**: Sophisticated error recovery and retry mechanisms
- **Extensible Architecture**: Plugin-based tool system and modular design

### Agent Types
- **ResearchAgent**: Specialized for information gathering, web research, and content analysis
- **TaskAgent**: Focused on data processing, file operations, and computational tasks
- **BaseAgent**: Abstract base class for creating custom agents

### Workflow Patterns
- **Sequential**: Step-by-step execution with dependency management
- **Parallel**: Concurrent execution for high-throughput scenarios
- **Conditional**: Decision-based execution with branching logic
- **Pipeline**: Data flow between steps with intermediate result passing

## 📋 Requirements

- Python 3.8+
- AsyncIO support
- Optional: PyYAML for configuration files

## 🛠 Installation

1. Clone or copy the multi-agent orchestration system:
```bash
cp -r src/multi_agent_orchestration /path/to/your/project/
```

2. Install dependencies:
```bash
cd /path/to/your/project/multi_agent_orchestration
pip install -r requirements.txt
```

## 🚀 Quick Start

### Running the Demo

```bash
# Run automated demo
python -m src.applications.multi_agent_orchestration.main demo

# Run interactive demo
python -m src.applications.multi_agent_orchestration.main demo --interactive
```

### Running Individual Workflows

```bash
# List available workflows
python -m src.applications.multi_agent_orchestration.main list

# Run specific workflow
python -m src.applications.multi_agent_orchestration.main workflow data_analysis
python -m src.applications.multi_agent_orchestration.main workflow parallel_processing
```

### Custom Workflows

```bash
# Create sample configuration
python -m src.applications.multi_agent_orchestration.main sample-config

# Run custom workflow
python -m src.applications.multi_agent_orchestration.main custom sample_workflow.yaml
```

## 📖 Usage Examples

### Basic Workflow Creation

```python
import asyncio
from src.applications.multi_agent_orchestration import (
    WorkflowOrchestrator,
    ResearchAgent,
    TaskAgent,
    MessageBroker,
    ExecutionPattern
)

async def main():
    # Initialize components
    message_broker = MessageBroker()
    orchestrator = WorkflowOrchestrator(message_broker)

    # Create and register agents
    research_agent = ResearchAgent("researcher")
    task_agent = TaskAgent("processor")

    await orchestrator.register_agent(research_agent)
    await orchestrator.register_agent(task_agent)

    # Define workflow steps
    steps = [
        {
            "step_id": "research",
            "agent_id": "researcher",
            "task_type": "web_research",
            "task_data": {"query": "AI trends 2024"}
        },
        {
            "step_id": "analyze",
            "agent_id": "processor",
            "task_type": "data_processing",
            "task_data": {"operation": "summarize"},
            "dependencies": ["research"]
        }
    ]

    # Create and execute workflow
    workflow_id = orchestrator.create_workflow(
        name="Research Pipeline",
        steps=steps,
        execution_pattern=ExecutionPattern.SEQUENTIAL
    )

    results = await orchestrator.execute_workflow(workflow_id)
    print(f"Workflow completed: {results['status']}")

    await orchestrator.shutdown()

asyncio.run(main())
```

### Custom Agent Development

```python
from src.applications.multi_agent_orchestration.agents.base_agent import BaseAgent
from src.applications.multi_agent_orchestration.common.types import TaskResult

class CustomAgent(BaseAgent):
    async def _execute_task_logic(self, task):
        task_type = task.get("task_type")

        if task_type == "custom_operation":
            # Implement custom logic
            result = self.perform_custom_operation(task.get("task_data", {}))
            return TaskResult(success=True, result=result)

        return TaskResult(success=False, error="Unsupported task type")

    def perform_custom_operation(self, data):
        # Your custom implementation
        return {"processed": True, "data": data}
```

### Configuration-Based Workflows

Create a YAML configuration file:

```yaml
agents:
  research_agent:
    type: research
    name: Research Specialist

  task_agent:
    type: task
    name: Data Processor

workflow:
  name: Custom Analysis Pipeline
  execution_pattern: sequential
  max_retries: 2
  timeout: 600

  steps:
    - step_id: gather_data
      agent_id: research_agent
      task_type: web_research
      task_data:
        query: "machine learning applications"
        max_results: 10
      timeout: 120

    - step_id: process_data
      agent_id: task_agent
      task_type: data_processing
      task_data:
        operation: "aggregate"
        options:
          group_by: ["category"]
      dependencies: ["gather_data"]
      timeout: 60

output_file: results.json
```

## 🏗 Architecture

### Core Components

```
multi_agent_orchestration/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Abstract base agent
│   ├── research_agent.py  # Research specialist
│   └── task_agent.py      # Task processor
├── orchestrator/          # Workflow orchestration
│   └── workflow_orchestrator.py
├── communication/         # Inter-agent messaging
│   └── message_broker.py
├── tools/                 # Pluggable tools
│   ├── base_tool.py
│   ├── web_search_tool.py
│   └── data_processor_tool.py
├── common/                # Shared types and utilities
│   └── types.py
├── examples/              # Demo applications
│   ├── workflow_examples.py
│   └── demo_application.py
└── tests/                 # Test suite
    └── test_orchestrator.py
```

### Key Design Patterns

- **Interface-Driven Design**: All components implement well-defined interfaces
- **Async-First Architecture**: Built for concurrent execution from the ground up
- **Plugin System**: Extensible tool system for adding new capabilities
- **Message-Based Communication**: Decoupled agent communication via message broker
- **Workflow as Code**: Define complex workflows programmatically or via configuration

## 🔧 Extension Points

### Adding New Agent Types

1. Inherit from `BaseAgent`
2. Implement `_execute_task_logic()` method
3. Register specialized tools if needed
4. Add to agent factory in main application

### Creating Custom Tools

1. Inherit from `BaseTool`
2. Implement `execute()` method
3. Register with agents that should use the tool

### New Workflow Patterns

1. Add execution pattern to `ExecutionPattern` enum
2. Implement execution logic in `WorkflowOrchestrator`
3. Add pattern-specific configuration options

## 📊 Monitoring & Metrics

The system provides comprehensive monitoring capabilities:

### Orchestrator Metrics
- Workflows executed/successful/failed
- Average execution time
- Active workflow count
- Execution history

### Agent Metrics
- Task execution counts by type
- Success/failure rates
- Performance metrics
- Tool usage statistics

### Accessing Metrics

```python
# Get orchestrator metrics
metrics = orchestrator.get_metrics()
print(f"Success rate: {metrics['workflows_successful'] / metrics['workflows_executed'] * 100:.1f}%")

# Get agent capabilities
capabilities = agent.get_capabilities()
print(f"Supported tasks: {capabilities['supported_task_types']}")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest src/multi_agent_orchestration/tests/

# Run specific test file
python -m pytest src/multi_agent_orchestration/tests/test_orchestrator.py

# Run with coverage
python -m pytest --cov=multi_agent_orchestration tests/
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Workflow Tests**: End-to-end workflow execution
- **Error Handling Tests**: Failure scenario validation

## 🚀 Production Deployment

### Configuration Management

```python
# Production configuration example
production_config = {
    "orchestrator": {
        "max_concurrent_workflows": 10,
        "default_timeout": 300,
        "retry_attempts": 3
    },
    "agents": {
        "research_agent": {
            "max_concurrent_tasks": 5,
            "rate_limit": "100/hour"
        },
        "task_agent": {
            "max_concurrent_tasks": 10,
            "work_directory": "/data/workspace"
        }
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/orchestration.log"
    }
}
```

### Scaling Considerations

- **Horizontal Scaling**: Deploy multiple orchestrator instances
- **Agent Distribution**: Distribute agents across multiple processes/machines
- **Message Broker**: Use external message broker for production (Redis, RabbitMQ)
- **Persistence**: Add database backend for workflow state persistence

### Monitoring Integration

```python
# Add monitoring hooks
orchestrator.add_event_handler("workflow_completed", send_metrics_to_monitoring)
orchestrator.add_event_handler("workflow_failed", send_alert)
```

## 🤝 Contributing

1. Follow the established patterns and interfaces
2. Add comprehensive tests for new functionality
3. Update documentation for new features
4. Use type hints and docstrings consistently

## 📝 License

This multi-agent orchestration system is provided as a template for building production systems. Adapt and modify according to your specific requirements.

## 🆘 Troubleshooting

### Common Issues

**Workflow Hangs**
- Check for circular dependencies in workflow steps
- Verify agent availability and responsiveness
- Review timeout configurations

**Agent Communication Failures**
- Ensure message broker is running
- Check agent registration status
- Verify network connectivity

**Performance Issues**
- Monitor concurrent task limits
- Review workflow execution patterns
- Check resource utilization

### Debug Mode

```bash
# Run with debug logging
python -m src.applications.multi_agent_orchestration.main demo --log-level DEBUG

# Enable detailed tracing
export ORCHESTRATION_DEBUG=1
python -m src.applications.multi_agent_orchestration.main workflow data_analysis
```
