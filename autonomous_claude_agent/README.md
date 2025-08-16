# Autonomous Claude Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](data/coverage/index.html)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](#testing)

A sophisticated autonomous agent that continuously improves itself by leveraging Claude Code MCP for analysis, modification, and enhancement. The agent operates in a feedback loop, learning from each iteration to become more effective at achieving its goals.

## Features

### 🤖 Core Capabilities
- **Self-Improvement**: Continuously analyzes and enhances its own capabilities
- **Autonomous Operation**: Operates independently with minimal human intervention
- **Multi-Modal Execution**: Supports sync, async, and batch processing modes
- **Adaptive Learning**: Learns from experiences and adapts strategies
- **Goal Decomposition**: Breaks down complex goals into manageable subtasks

### 🛡️ Safety & Governance
- **Resource Monitoring**: Tracks CPU, memory, disk usage, and API limits
- **Safety Rules**: Prevents dangerous self-modifications
- **Approval System**: Requires approval for sensitive operations
- **Audit Logging**: Comprehensive logging of all actions
- **Graceful Degradation**: Handles resource limits and errors gracefully

### 🔍 Research & Discovery
- **Capability Discovery**: Automatically discovers new capabilities
- **Web Research**: Searches for solutions and best practices
- **Documentation Analysis**: Analyzes technical documentation
- **Pattern Recognition**: Identifies and learns from successful patterns

### 📊 Monitoring & Analytics
- **Real-time Dashboard**: Web-based monitoring interface
- **Performance Metrics**: Tracks success rates, iteration times, improvements
- **Health Checks**: Monitors agent and system health
- **Alert Management**: Notifications for important events

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Claude API access (for full functionality)
- 4GB+ RAM recommended
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd autonomous_claude_agent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the agent:**
```bash
cp config/settings.yaml.example config/settings.yaml
# Edit config/settings.yaml with your settings
```

4. **Set up environment variables:**
```bash
export CLAUDE_API_KEY="your-api-key-here"
export CLAUDE_AGENT_MODE="autonomous"
```

### Basic Usage

**Start the agent with a simple goal:**
```bash
python launch.py --goal "Analyze Python code quality in the src/ directory"
```

**With custom configuration:**
```bash
python launch.py \
  --goal "Implement a web scraper for news articles" \
  --config config/production.yaml \
  --max-iterations 100 \
  --mode supervised
```

**Resume from checkpoint:**
```bash
python launch.py \
  --goal "Continue previous task" \
  --checkpoint checkpoint-abc123
```

## Configuration

### Basic Configuration

The agent is configured via YAML files. Here's a minimal configuration:

```yaml
# config/settings.yaml
max_iterations: 1000
mode: autonomous

claude:
  max_concurrent: 5
  timeout: 300
  rate_limits:
    requests_per_minute: 60
    tokens_per_day: 100000

limits:
  memory_mb: 4096
  cpu_percent: 80
  daily_tokens: 100000

safety:
  allow_file_modifications: true
  require_approval_for: ['delete', 'system_command']
  max_recursion_depth: 5

logging:
  level: INFO
  file: data/logs/agent.log
```

### Advanced Configuration

For production deployments, see `config/production.yaml` for advanced settings including:
- Resource limits and quotas
- Security policies
- Monitoring configuration
- Research and discovery settings

## Usage Examples

### Example 1: Code Analysis and Improvement

```bash
python launch.py --goal "Analyze and improve the performance of the data processing pipeline"
```

The agent will:
1. Analyze the existing codebase
2. Identify performance bottlenecks
3. Research optimization techniques
4. Implement improvements
5. Validate the changes
6. Learn from the results

### Example 2: Building a New Feature

```bash
python launch.py --goal "Implement user authentication with JWT tokens"
```

The agent will:
1. Research JWT authentication patterns
2. Design the authentication system
3. Generate the implementation
4. Create comprehensive tests
5. Document the new feature
6. Integrate with existing code

### Example 3: Debugging and Error Resolution

```bash
python launch.py --goal "Fix the ImportError in the data_processor module"
```

The agent will:
1. Analyze the error and its context
2. Trace dependencies and imports
3. Research solutions for the specific error
4. Apply the fix
5. Test the resolution
6. Learn the pattern for future reference

## Architecture

The agent follows a modular architecture with clear separation of concerns:

```
src/
├── core/                 # Core agent functionality
│   ├── agent.py         # Main autonomous agent
│   ├── claude_client.py # Claude API integration
│   ├── state_manager.py # State persistence
│   └── error_recovery.py# Error handling
├── capabilities/        # Dynamic capability system
├── learning/           # Machine learning and pattern recognition
├── modification/       # Self-modification capabilities
├── research/          # Research and discovery
├── governance/        # Safety and resource management
├── monitoring/        # Health checks and metrics
└── utils/            # Utilities and helpers
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## API Reference

### Core Agent Class

```python
from src.core.agent import AutonomousAgent

# Create agent
agent = AutonomousAgent(config, mode="autonomous")

# Run with goal
await agent.run("Improve code quality")

# Execute single iteration
context = ExecutionContext(iteration=1, goal="test", state=AgentState.EXECUTING)
result = await agent.execute_iteration(context)

# Save/restore checkpoints
checkpoint_id = await agent.save_checkpoint(context)
await agent.resume_from_checkpoint(checkpoint_id, "new goal")
```

### Configuration Management

```python
from src.utils.config_loader import load_config

config = load_config("config/settings.yaml")
agent = AutonomousAgent(config)
```

### Capability System

```python
# Register new capability
await agent.capability_registry.register("new_capability", handler_function)

# Execute capability
result = await agent.execute_capability("capability_name", {"param": "value"})

# Discover capabilities
capabilities = await agent.capability_discovery.discover_capabilities()
```

## Testing

The project includes comprehensive test coverage with multiple test categories:

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m stress       # Stress tests only

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest -m performance --durations=10
```

### Test Categories

- **Unit Tests**: Fast, isolated tests of individual components
- **Integration Tests**: Tests of component interactions
- **Stress Tests**: Resource-intensive and long-running tests
- **Performance Tests**: Benchmarking and performance validation
- **Network Tests**: Tests requiring network access
- **Claude Tests**: Tests requiring Claude API access (skipped by default)

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── stress/           # Stress tests
├── fixtures/         # Test data and fixtures
├── conftest.py       # Pytest configuration
└── test_agent.py     # Main agent tests
```

## Monitoring

### Web Dashboard

Access the real-time dashboard at `http://localhost:8080` when the agent is running:

- **Agent Status**: Current state, iteration, success rate
- **Resource Usage**: CPU, memory, disk, API usage
- **Recent Activities**: Latest actions and results
- **Performance Metrics**: Charts and graphs
- **Logs**: Real-time log streaming

### Health Checks

Monitor agent health via HTTP endpoints:

```bash
# Agent status
curl http://localhost:8080/health

# Detailed metrics
curl http://localhost:8080/metrics

# Performance data
curl http://localhost:8080/performance
```

### Logging

Comprehensive logging at multiple levels:

```python
# Configure logging
import logging
from src.utils.logger import setup_logging

logger = setup_logging({
    'level': 'INFO',
    'file': 'data/logs/agent.log',
    'max_bytes': 10485760,
    'backup_count': 5
})
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t autonomous-claude-agent .

# Run container
docker run -d \
  --name claude-agent \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e CLAUDE_API_KEY=your-key \
  autonomous-claude-agent \
  --goal "Your goal here"
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f docker/k8s/

# Check status
kubectl get pods -l app=claude-agent

# View logs
kubectl logs -f deployment/claude-agent
```

### Production Considerations

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **API Rate Limits**: Configure rate limiting for Claude API
3. **Data Persistence**: Use persistent volumes for data
4. **Monitoring**: Set up external monitoring and alerting
5. **Security**: Review safety rules and approval requirements

## Troubleshooting

### Common Issues

**Agent not starting:**
```bash
# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/settings.yaml')))"

# Verify dependencies
pip install -r requirements.txt

# Check logs
tail -f data/logs/agent.log
```

**High resource usage:**
```bash
# Check resource limits
curl http://localhost:8080/metrics

# Monitor in real-time
python -c "from src.monitoring.dashboard import run_monitoring; run_monitoring()"
```

**API errors:**
```bash
# Verify API key
export CLAUDE_API_KEY="your-key"

# Test API connection
python -c "from src.core.claude_client import ClaudeClient; client = ClaudeClient({}); print('OK')"
```

### Performance Optimization

1. **Adjust iteration limits**: Lower `max_iterations` for faster cycles
2. **Optimize resource limits**: Tune memory and CPU limits
3. **Use batch processing**: Enable batch mode for multiple tasks
4. **Cache research results**: Increase `cache_ttl_hours` for research
5. **Parallel execution**: Increase `max_concurrent` for Claude requests

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
isort src/ tests/
pylint src/

# Run full test suite
pytest --cov=src
```

### Code Standards

- Follow PEP 8 style guidelines
- Maintain test coverage above 80%
- Add docstrings to all public functions
- Use type hints where appropriate
- Write comprehensive tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

### Reporting Security Issues

Please report security issues privately to [security@example.com](mailto:security@example.com).

### Security Features

- **Input validation** for all external inputs
- **Resource limits** to prevent resource exhaustion
- **Safety rules** to prevent dangerous operations
- **Audit logging** for security monitoring
- **Approval system** for sensitive operations

## Changelog

### Version 1.0.0 (2025-01-15)

- Initial release
- Core autonomous agent functionality
- Claude Code integration
- Comprehensive test suite
- Web dashboard and monitoring
- Docker and Kubernetes support

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Support

- **Documentation**: [Full documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/example/autonomous-claude-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/example/autonomous-claude-agent/discussions)
- **Email**: [support@example.com](mailto:support@example.com)

## Acknowledgments

- [Anthropic Claude](https://www.anthropic.com/claude) for the powerful language model
- [Claude Code MCP](https://github.com/anthropics/claude-mcp) for the integration framework
- The open-source community for inspiration and contributions

---

**Note**: This agent is designed for autonomous operation but should be used responsibly. Always review safety settings and monitor agent behavior in production environments.