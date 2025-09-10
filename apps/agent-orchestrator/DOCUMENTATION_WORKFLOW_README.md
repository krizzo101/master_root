# Documentation Workflow System

A comprehensive agent orchestration system for automated documentation generation with specialized agents, checkpointing, and resumption capabilities.

## Overview

The Documentation Workflow System provides a standardized way to generate complete documentation for any application using specialized AI agents. It supports multiple documentation types, templates, and includes robust checkpoint/resumption capabilities for long-running workflows.

## Quick Start

Generate comprehensive documentation for any application:

```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
python run_orchestrator_task.py --task-type system-documentation --app-name my-app --app-root /path/to/app
```

## Architecture

### Core Components

1. **Documentation Workflow** (`src/workflows/documentation_workflow.py`)
   - Orchestrates specialized documentation agents
   - Manages task dependencies and execution flow
   - Handles output coordination and integration

2. **Execution Plans** (`src/workflows/execution_plans.py`)
   - Pre-configured workflow templates
   - Checkpoint management system
   - Resumption capabilities

3. **Resumable Orchestrator** (`src/workflows/resumable_orchestrator.py`)
   - Extends base orchestrator with checkpointing
   - Automatic failure recovery
   - Progress tracking and metrics

### Specialized Agents

The system uses specialized agents for different documentation tasks:

- **Code Analyzer**: Deep codebase analysis and information extraction
- **Technical Writer**: README.md and overview documentation
- **API Documenter**: Complete API reference documentation
- **Architecture Analyst**: System design and architecture documentation
- **User Guide Writer**: End-user documentation and guides
- **Deployment Specialist**: Deployment and operations documentation
- **Integration Validator**: Final validation and integration

## Workflow Templates

### Comprehensive Template
Full documentation suite with all components:
- README.md with project overview
- API_REFERENCE.md with complete API docs
- ARCHITECTURE.md with system design
- USER_GUIDE.md with user documentation
- DEVELOPER_GUIDE.md with development guide
- DEPLOYMENT.md with deployment instructions

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app --template comprehensive
```

### Standard Template
Essential documentation for most projects:
- README.md
- API_REFERENCE.md
- DEVELOPER_GUIDE.md

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app --template standard
```

### Minimal Template
Basic README-only documentation:
- README.md

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app --template minimal
```

### API-Focused Template
API documentation with examples:
- README.md
- API_REFERENCE.md (comprehensive)
- DEVELOPER_GUIDE.md

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app --template api-focused
```

## Command Line Usage

### Main Task Runner

```bash
# Basic documentation generation
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app

# Custom template and output directory
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app \
  --template standard --output-dir /custom/docs/path

# Custom configuration
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app \
  --template comprehensive \
  --detail-level standard \
  --max-parallel 3 \
  --checkpoint-interval 2
```

### Checkpoint Management

```bash
# List available checkpoints
python run_orchestrator_task.py --list-checkpoints

# List checkpoints for specific app
python run_orchestrator_task.py --list-checkpoints --app-name my-app

# Show checkpoint details
python run_orchestrator_task.py --checkpoint-details checkpoint_id_here

# Resume from checkpoint
python run_orchestrator_task.py --resume-checkpoint checkpoint_id_here
```

### Resume Script

```bash
# Resume from checkpoint ID
python resume_orchestrator.py checkpoint_sysdoc_myapp_20231201_143022

# List all available checkpoints
python resume_orchestrator.py --list-checkpoints

# Show checkpoint details
python resume_orchestrator.py --details checkpoint_sysdoc_myapp_20231201_143022
```

## Configuration Options

### Documentation Options

- `--include-api-docs`: Include API reference documentation
- `--include-architecture`: Include architecture documentation
- `--include-deployment`: Include deployment documentation
- `--include-user-guide`: Include user guide documentation
- `--detail-level`: Level of detail (minimal, standard, comprehensive)

### Execution Control

- `--max-parallel`: Maximum parallel agent executions (default: 5)
- `--checkpoint-interval`: Create checkpoint every N completed tasks (default: 3)
- `--keep-workspace`: Keep workspace directory after completion

### Debug and Logging

- `--verbose`: Enable verbose logging
- `--debug`: Enable debug logging

## Output Structure

Documentation is generated in the specified output directory (default: `{app_root}/docs/`):

```
docs/
├── README.md                    # Project overview and quick start
├── API_REFERENCE.md            # Complete API documentation
├── ARCHITECTURE.md             # System design and architecture
├── USER_GUIDE.md               # End-user documentation
├── DEVELOPER_GUIDE.md          # Development guide (integration output)
├── DEPLOYMENT.md               # Deployment and operations
└── documentation_workflow_summary.json  # Execution summary
```

## Checkpointing and Resumption

The system automatically creates checkpoints during execution:

1. **Automatic Checkpoints**: Created every N completed tasks (configurable)
2. **Phase Checkpoints**: Created at end of each workflow phase
3. **Failure Checkpoints**: Created when workflow encounters errors

### Checkpoint Structure

Checkpoints contain:
- Completed tasks list
- Failed tasks list
- Pending tasks list
- Workflow configuration
- Execution context and results

### Resumption Process

When resuming from a checkpoint:
1. Loads checkpoint and execution plan
2. Recreates orchestrator with same configuration
3. Continues execution from pending tasks
4. Maintains all previous results and context

## Integration with Existing Orchestrator

The documentation workflow integrates seamlessly with the existing GenericOrchestrator:

1. **Task Generation**: Creates AgentTask objects for specialized agents
2. **Dependency Management**: Uses orchestrator's dependency system
3. **Parallel Execution**: Leverages orchestrator's parallel execution
4. **Token Management**: Uses existing token pool system
5. **MCP Integration**: Works with existing MCP configuration

## Error Handling

The system includes comprehensive error handling:

- **Task-Level Errors**: Individual agent failures are isolated
- **Dependency Failures**: Failed dependencies block dependent tasks
- **Checkpoint Recovery**: Can resume from any checkpoint after failures
- **Partial Results**: Successful tasks are preserved even if others fail

## Monitoring and Metrics

Each workflow execution provides:

- Real-time progress tracking
- Task success/failure metrics
- Execution time measurements
- Detailed error reporting
- Checkpoint creation logs

## Example Workflows

### Generate Documentation for Python Package

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-python-package \
  --app-root /home/user/my-python-package \
  --template comprehensive \
  --include-api-docs \
  --include-deployment
```

### API Service Documentation

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-api-service \
  --app-root /home/user/my-api-service \
  --template api-focused \
  --detail-level comprehensive
```

### Quick README Generation

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-project \
  --app-root /home/user/my-project \
  --template minimal
```

## Extending the System

### Adding New Documentation Types

1. Create new agent function in `DocumentationWorkflow`
2. Add to `create_documentation_tasks()` method
3. Update execution plan templates as needed

### Custom Templates

1. Add new template method to `ExecutionPlanTemplates`
2. Define phases, dependencies, and configuration
3. Register in `ExecutionPlanManager.create_plan_from_template()`

### New Specialized Agents

1. Create agent function following existing patterns
2. Define clear prompt with role specialization
3. Set appropriate dependencies and context requirements

## Troubleshooting

### Common Issues

1. **Checkpoint Not Found**: Use `--list-checkpoints` to find available checkpoints
2. **Task Dependencies Failed**: Check logs for specific agent failures
3. **Token Pool Exhausted**: Reduce `--max-parallel` setting
4. **MCP Configuration Issues**: Verify MCP servers are available

### Debug Mode

Enable debug logging for detailed execution information:

```bash
python run_orchestrator_task.py --task-type system-documentation \
  --app-name my-app --app-root /path/to/app --debug
```

### Manual Checkpoint Recovery

If automated resumption fails, you can manually inspect checkpoint files:

```bash
# View checkpoint contents
cat orchestrator_output/20231201_143022/checkpoints/checkpoint_sysdoc_myapp_20231201_143022.json

# Get checkpoint details
python resume_orchestrator.py --details checkpoint_sysdoc_myapp_20231201_143022
```

## Performance Considerations

- **Parallel Execution**: Adjust `--max-parallel` based on available tokens and system resources
- **Checkpoint Frequency**: More frequent checkpoints provide better recovery but slight overhead
- **Template Selection**: Choose appropriate template complexity for your needs
- **Token Management**: Monitor token usage with multiple parallel agents

## Future Enhancements

Planned improvements include:
- Additional documentation types (tutorials, examples, etc.)
- Multi-language documentation support
- Integration with documentation hosting platforms
- Automated testing of generated documentation
- Template customization via configuration files
