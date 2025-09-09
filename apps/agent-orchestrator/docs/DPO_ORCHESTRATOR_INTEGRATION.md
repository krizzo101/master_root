# DPO Orchestrator Integration Layer

## Overview

The DPO Orchestrator Integration Layer provides seamless connectivity between the Development Process Orchestrator (DPO) system and the GenericOrchestrator execution engine. This integration enables intelligent workflow generation, parallel agent execution, real-time monitoring, and comprehensive results harvesting.

## Architecture

### Component Hierarchy

```
DPO Request (Natural Language)
    ↓
DPO Intelligence Integration (Enhancement)
    ↓
Enhanced DPO Workflow (15-25 agents)
    ↓
DPO Orchestrator Integration Layer ← [This Component]
    ↓
GenericOrchestrator (Execution)
    ↓
Results & Knowledge Extraction
```

### Key Components

1. **DPOOrchestrator Class**
   - Main integration controller
   - Workflow lifecycle management
   - Progress monitoring
   - Results harvesting

2. **Workflow Submission System**
   - Converts DPO workflows to orchestrator tasks
   - Manages dependencies and sequencing
   - Handles project organization

3. **Progress Monitoring**
   - Real-time task tracking
   - WebSocket broadcasting
   - Dashboard integration
   - ETA calculations

4. **Results Harvesting**
   - Deliverable collection
   - Knowledge extraction
   - Metrics aggregation
   - Error tracking

## API Reference

### Core Class: DPOOrchestrator

```python
class DPOOrchestrator:
    def __init__(self,
                 output_base_dir: str = "output/dpo_workflows",
                 max_parallel_agents: int = 10,
                 enable_websocket: bool = True,
                 websocket_port: int = 8765,
                 dashboard_callback: Optional[Callable] = None)
```

### Primary Methods

#### submit_development_request

Submit a natural language development request for processing.

```python
async def submit_development_request(
    request: str,
    project_type: str = "web_app",
    complexity: str = "moderate",
    context: Optional[Dict] = None
) -> str
```

**Parameters:**
- `request`: Natural language description of the development task
- `project_type`: One of: "web_app", "api", "cli", "library", "integration"
- `complexity`: One of: "simple", "moderate", "complex"
- `context`: Additional project context (framework, database, features, etc.)

**Returns:**
- `workflow_id`: Unique identifier for tracking the workflow

**Example:**
```python
workflow_id = await orchestrator.submit_development_request(
    request="Build a task management API with authentication",
    project_type="api",
    complexity="moderate",
    context={
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "authentication": "JWT"
    }
)
```

#### get_workflow_status

Get current workflow status and progress.

```python
async def get_workflow_status(workflow_id: str) -> Dict
```

**Returns:**
```python
{
    'workflow_id': 'DPO_xxx',
    'status': 'running',  # pending|initializing|running|completed|failed|cancelled
    'progress': {
        'total_tasks': 25,
        'completed_tasks': 15,
        'failed_tasks': 0,
        'progress_percentage': 60.0,
        'current_phase': 'implementation',
        'estimated_completion': '2025-09-09T10:30:00'
    }
}
```

#### get_workflow_results

Retrieve completed workflow results.

```python
async def get_workflow_results(workflow_id: str) -> Optional[WorkflowResults]
```

**Returns:**
```python
WorkflowResults(
    workflow_id='DPO_xxx',
    status=WorkflowStatus.COMPLETED,
    duration_seconds=1234.5,
    deliverables=['file1.py', 'file2.js', ...],
    extracted_knowledge=[...],
    metrics={
        'success_rate': 0.95,
        'total_tasks': 25,
        'completed_tasks': 24,
        'failed_tasks': 1
    }
)
```

#### cancel_workflow

Cancel a running workflow.

```python
async def cancel_workflow(workflow_id: str) -> bool
```

## REST API Endpoints

The integration layer provides REST API endpoints when FastAPI is available:

### Submit Workflow
```
POST /api/v1/workflows/submit
Content-Type: application/json

{
    "request": "Build a user management system",
    "project_type": "api",
    "complexity": "moderate",
    "context": {...}
}
```

### Get Status
```
GET /api/v1/workflows/{workflow_id}/status
```

### Get Results
```
GET /api/v1/workflows/{workflow_id}/results
```

### Cancel Workflow
```
POST /api/v1/workflows/{workflow_id}/cancel
```

### Resume from Checkpoint
```
POST /api/v1/workflows/{workflow_id}/resume
Content-Type: application/json

{
    "checkpoint_path": "/path/to/checkpoint.json"
}
```

## WebSocket Integration

Real-time updates are broadcast via WebSocket when enabled:

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

### Message Types

#### Progress Update
```json
{
    "type": "progress_update",
    "workflow_id": "DPO_xxx",
    "progress": {
        "completed_tasks": 15,
        "total_tasks": 25,
        "progress_percentage": 60.0
    }
}
```

#### Status Update
```json
{
    "type": "status_update",
    "workflow_id": "DPO_xxx",
    "status": "completed"
}
```

## Workflow Conversion Process

### 1. DPO Workflow to Orchestrator Tasks

The integration layer converts enhanced DPO workflows into executable orchestrator tasks:

```python
Enhanced Workflow Phase → Multiple Agent Tasks
    - Phase dependencies → Task dependencies
    - Enhancements → Task prompts
    - Quality gates → Task validation
    - Deliverables → Output organization
```

### 2. Agent Prompt Generation

Each agent receives a comprehensive prompt including:
- Original development request
- Phase-specific objectives
- Enhancements to implement
- Success criteria
- Quality requirements
- Project context

### 3. Dependency Management

Tasks are organized with proper dependencies:
- Sequential phases (design → implementation → testing)
- Parallel execution within phases
- Cross-phase dependencies for integration points

## Progress Monitoring

### Real-time Tracking

The integration layer monitors:
- Task execution status
- Phase completion
- Agent performance
- Resource utilization
- Error occurrences

### Dashboard Integration

Progress updates are sent to dashboard via callback:

```python
def dashboard_callback(state_data: Dict):
    # state_data contains:
    # - event: workflow_started|progress|completed
    # - workflow_id
    # - metrics
    # - current status
```

## Results Harvesting

### Deliverable Collection

The system automatically collects:
- Generated source code files
- Documentation
- Configuration files
- Test suites
- Build artifacts

### Knowledge Extraction

Extracts reusable knowledge:
- Design patterns discovered
- Best practices identified
- Integration points
- Performance optimizations
- Common solutions

### Metrics Aggregation

Comprehensive metrics include:
- Task success rates
- Execution duration
- Resource usage
- Error frequency
- Quality gate results

## Error Handling

### Failure Recovery

The integration layer handles:
- Individual task failures
- Phase-level failures
- Dependency deadlocks
- Resource exhaustion
- Timeout conditions

### Checkpoint & Resume

Workflows can be resumed from checkpoints:
- Checkpoint created after each phase
- Preserves completed task results
- Restores workflow state
- Continues from last successful point

## Configuration

### Environment Variables

```bash
# Output directory for workflows
DPO_OUTPUT_DIR=/path/to/output

# Maximum parallel agents
DPO_MAX_PARALLEL=10

# WebSocket configuration
DPO_WEBSOCKET_ENABLED=true
DPO_WEBSOCKET_PORT=8765

# Dashboard integration
DPO_DASHBOARD_URL=http://localhost:3000
```

### Project Organization

Workflows create organized project structures:

```
/apps/dpo_PROJECT_NAME/
├── src/              # Source code
├── tests/            # Test suites
├── docs/             # Documentation
├── config/           # Configuration
├── scripts/          # Utility scripts
└── deliverables/     # Final outputs
```

## Usage Examples

### Basic Workflow Submission

```python
import asyncio
from dpo_orchestrator_integration import DPOOrchestrator

async def main():
    # Initialize orchestrator
    orchestrator = DPOOrchestrator()

    # Submit workflow
    workflow_id = await orchestrator.submit_development_request(
        request="Build a REST API for blog management",
        project_type="api",
        complexity="simple"
    )

    # Monitor progress
    while True:
        status = await orchestrator.get_workflow_status(workflow_id)
        print(f"Progress: {status['progress']['progress_percentage']:.1f}%")

        if status['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(5)

    # Get results
    results = await orchestrator.get_workflow_results(workflow_id)
    print(f"Deliverables: {len(results.deliverables)}")

asyncio.run(main())
```

### Complex Multi-Phase Workflow

```python
workflow_id = await orchestrator.submit_development_request(
    request="""
    Build a comprehensive e-commerce platform with:
    - Product catalog
    - Shopping cart
    - Payment processing
    - Order management
    - Admin dashboard
    """,
    project_type="web_app",
    complexity="complex",
    context={
        "frontend": "React",
        "backend": "Node.js",
        "database": "PostgreSQL",
        "payment": "Stripe"
    }
)
```

### WebSocket Monitoring

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'progress_update') {
        updateProgressBar(data.progress.progress_percentage);
        updateTaskCount(data.progress.completed_tasks, data.progress.total_tasks);
    }
};
```

## Performance Optimization

### Parallel Execution

- Up to 15 agents can execute in parallel (configurable)
- Token pool management prevents API rate limiting
- Intelligent task scheduling based on dependencies

### Resource Management

- Memory-efficient task queuing
- Automatic cleanup of completed tasks
- Result streaming for large outputs

### Caching

- Intelligence review results cached
- Template reuse across similar requests
- Knowledge base for pattern recognition

## Testing

### Unit Tests

Test individual components:

```bash
python -m pytest tests/test_dpo_orchestrator.py
```

### Integration Tests

Test complete workflow:

```bash
python test_dpo_integration.py
```

### Load Testing

Test concurrent workflows:

```bash
python test_dpo_load.py --workflows 10 --parallel 3
```

## Troubleshooting

### Common Issues

1. **Workflow Stuck in Pending**
   - Check token pool availability
   - Verify orchestrator is running
   - Review dependency deadlocks

2. **High Failure Rate**
   - Check agent prompts
   - Verify API tokens
   - Review error logs

3. **Slow Progress**
   - Increase parallel agents
   - Optimize task dependencies
   - Check resource limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

orchestrator = DPOOrchestrator()
```

### Log Files

Logs are stored in:
- `output/WORKFLOW_ID/orchestrator.log` - Main orchestrator log
- `output/WORKFLOW_ID/agents/TASK_ID.log` - Individual agent logs
- `output/WORKFLOW_ID/deliverables/workflow_completion_report.json` - Final report

## Best Practices

### Request Formulation

1. **Be Specific**: Provide detailed requirements
2. **Include Context**: Specify frameworks, databases, constraints
3. **Set Complexity**: Match complexity to actual project scope
4. **Define Success**: Include measurable success criteria

### Workflow Management

1. **Monitor Progress**: Use WebSocket or polling for real-time updates
2. **Handle Failures**: Implement retry logic for failed workflows
3. **Collect Results**: Process deliverables and extract knowledge
4. **Clean Up**: Remove completed workflow data periodically

### Integration Patterns

1. **Dashboard Integration**: Use callbacks for UI updates
2. **CI/CD Pipeline**: Integrate with build systems
3. **Knowledge Base**: Store extracted patterns for reuse
4. **Metrics Collection**: Track performance over time

## Future Enhancements

### Planned Features

1. **Advanced Resume**: Modify workflow during execution
2. **Workflow Templates**: Reusable workflow definitions
3. **Multi-Project**: Coordinate related projects
4. **Resource Optimization**: Dynamic agent allocation
5. **Quality Analysis**: Automated code quality assessment

### Extensibility

The integration layer supports extensions through:
- Custom task generators
- Result processors
- Quality gates
- Knowledge extractors
- Dashboard integrations

## Support

For issues, questions, or contributions:

1. Check documentation: `/docs/DPO_ORCHESTRATOR_INTEGRATION.md`
2. Review examples: `/examples/dpo_integration/`
3. Run tests: `python test_dpo_integration.py`
4. Check logs: `output/WORKFLOW_ID/orchestrator.log`

## License

This component is part of the Agent Orchestrator system.
© 2025 Agent Orchestrator Team
