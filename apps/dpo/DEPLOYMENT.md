# DPO System Deployment Guide

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Ecosystem Integration](#ecosystem-integration)
5. [Configuration](#configuration)
6. [Validation & Testing](#validation--testing)
7. [Operations](#operations)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

## Deployment Overview

The DPO system deployment consists of:

- **Core System**: DPO controller, intelligence engine, and template system
- **Integration Layer**: Connections to agent-orchestrator and MCP tools
- **Configuration**: System settings and customization
- **Templates**: Pre-built and custom workflow templates
- **Monitoring**: Dashboard and metrics collection

### Deployment Architecture

```
master_root/
├── apps/
│   ├── dpo/                    # DPO System (THIS PACKAGE)
│   │   ├── src/                # Core components
│   │   ├── templates/          # Workflow templates
│   │   ├── config/             # Configuration
│   │   └── bin/                # CLI tools
│   ├── agent-orchestrator/     # Agent orchestration system
│   └── session-optimizer/      # Session optimization tools
└── .claude/
    └── knowledge/              # Knowledge base integration
```

## System Requirements

### Minimum Requirements

- **OS**: Linux, macOS, or WSL2 on Windows
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

### Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check pip
pip3 --version

# Check git
git --version

# Verify master_root location
ls /home/opsvi/master_root/apps/
```

### Required Components

1. **Agent Orchestrator**: Must be installed at `/home/opsvi/master_root/apps/agent-orchestrator`
2. **Python Environment**: Miniconda or system Python 3.8+
3. **MCP Tools** (Optional): For enhanced features

## Installation Methods

### Method 1: Automated Installation (Recommended)

```bash
# Navigate to DPO directory
cd /home/opsvi/master_root/apps/dpo

# Run installation script
./install.sh

# Verify installation
dpo --version
```

### Method 2: Make Installation

```bash
# Using Makefile
cd /home/opsvi/master_root/apps/dpo

# Full deployment (install + integrate + validate)
make deploy

# Or step by step
make install
make integrate
make validate
```

### Method 3: Manual Installation

```bash
# Create virtual environment
python3 -m venv ~/.dpo/venv
source ~/.dpo/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install DPO package
pip install -e .

# Set up configuration
mkdir -p ~/.dpo/config
cp config/default_config.json ~/.dpo/config/dpo_config.json

# Install templates
mkdir -p ~/.dpo/templates
cp templates/*.json ~/.dpo/templates/

# Create symlinks
ln -sf ~/.dpo/venv/bin/dpo /usr/local/bin/dpo

# Run integration
python scripts/integrate_orchestrator.py
```

### Method 4: Docker Deployment

```bash
# Build Docker image
docker build -t dpo:latest .

# Run container
docker run -d \
  --name dpo-system \
  -p 8765:8765 \
  -p 8080:8080 \
  -v $(pwd):/app \
  -v ~/.dpo:/root/.dpo \
  dpo:latest
```

## Ecosystem Integration

### Agent Orchestrator Integration

```bash
# Automatic integration
python scripts/integrate_orchestrator.py

# Verify integration
python -c "from src.dpo_orchestrator_integration import DPOOrchestrator; print('✓ Integration successful')"
```

### MCP Tools Integration

```bash
# Check MCP configuration
cat ~/.mcp.json

# Required MCP servers:
# - knowledge: For knowledge base
# - shell_exec: For command execution
# - web_search: For web queries
# - tech_docs: For documentation
```

### Knowledge Base Setup

```bash
# Initialize knowledge base
mkdir -p ~/.claude/knowledge/dpo

# Link to DPO
ln -sf ~/.claude/knowledge ~/.dpo/knowledge

# Test knowledge integration
python -c "import mcp; print('✓ MCP available')"
```

### Session Optimizer Integration

```bash
# Link session optimizer
ln -sf /home/opsvi/master_root/apps/session-optimizer ~/.dpo/session_optimizer

# Enable in configuration
dpo configure --enable-session-optimizer
```

## Configuration

### Configuration Files

1. **Main Configuration**: `~/.dpo/config/dpo_config.json`
2. **Integration Config**: `~/.dpo/config/integration.json`
3. **Templates**: `~/.dpo/templates/*.json`

### Configuration Structure

```json
{
  "orchestration": {
    "output_base_dir": "~/dpo_output",
    "max_parallel_agents": 10,
    "checkpoint_interval": 300
  },
  "communication": {
    "websocket_port": 8765,
    "enable_dashboard": true
  },
  "intelligence": {
    "enable_intelligence": true,
    "enhancement_threshold": 0.7
  },
  "templates": {
    "template_library_path": "~/.dpo/templates"
  }
}
```

### Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export DPO_HOME="$HOME/.dpo"
export DPO_CONFIG="$HOME/.dpo/config/dpo_config.json"
export DPO_LOG_LEVEL="INFO"
export PYTHONPATH="$PYTHONPATH:/home/opsvi/master_root/apps/dpo/src"
```

### CLI Configuration

```bash
# View current configuration
dpo configure --show

# Update settings
dpo configure --max-agents 15
dpo configure --websocket-port 8766
dpo configure --enable-dashboard

# Reset to defaults
dpo configure --reset
```

## Validation & Testing

### Deployment Validation

```bash
# Run comprehensive validation
python tests/test_deployment.py

# Or using Make
make validate

# Check specific components
python -m pytest tests/test_deployment.py::TestDPODeployment::test_directory_structure
```

### Integration Testing

```bash
# Test orchestrator integration
python tests/test_integration.py

# Test template validation
make test-templates

# Test CLI functionality
dpo build "test request" --dry-run
```

### Performance Testing

```bash
# Run performance benchmarks
python tests/test_performance.py

# Monitor resource usage
dpo metrics --format json
```

## Operations

### Starting Services

```bash
# Start DPO server
dpo server

# Or as background service
nohup dpo server > ~/.dpo/logs/server.log 2>&1 &

# Start with custom configuration
dpo server --config ~/.dpo/config/production.json
```

### Dashboard Access

```bash
# Start dashboard
dpo dashboard

# Access at http://localhost:8080

# Custom port
dpo dashboard --port 8090
```

### Monitoring

```bash
# View system metrics
dpo metrics

# Continuous monitoring
watch -n 5 "dpo status --all"

# Export metrics
dpo metrics --format csv > metrics.csv
```

### Logging

```bash
# View logs
tail -f ~/.dpo/logs/dpo.log

# Filter logs
grep ERROR ~/.dpo/logs/dpo.log

# Rotate logs
logrotate ~/.dpo/config/logrotate.conf
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Daily: Check system health
dpo status
dpo metrics --period today

# Weekly: Clean old outputs
find ~/dpo_output -type f -mtime +7 -delete

# Monthly: Update dependencies
pip install --upgrade -r requirements.txt

# Quarterly: Full system validation
make validate
```

### Backup Procedures

```bash
# Backup configuration and templates
tar czf dpo_backup_$(date +%Y%m%d).tar.gz \
  ~/.dpo/config \
  ~/.dpo/templates \
  ~/.dpo/knowledge

# Backup outputs
rsync -av ~/dpo_output/ /backup/dpo_output/
```

### Updates and Upgrades

```bash
# Update DPO system
cd /home/opsvi/master_root/apps/dpo
git pull
pip install --upgrade -e .

# Update templates
cp templates/*.json ~/.dpo/templates/

# Verify update
dpo --version
```

## Troubleshooting

### Common Issues and Solutions

#### Installation Failures

```bash
# Problem: Permission denied
Solution: Use sudo for system-wide installation or install to user directory

# Problem: Python version mismatch
Solution: Use pyenv or conda to install Python 3.8+

# Problem: Missing dependencies
Solution: pip install --upgrade pip setuptools wheel
```

#### Integration Issues

```bash
# Problem: Orchestrator not found
Solution: Verify orchestrator installation at /home/opsvi/master_root/apps/agent-orchestrator

# Problem: MCP tools unavailable
Solution: Check ~/.mcp.json configuration

# Problem: Import errors
Solution: Update PYTHONPATH to include DPO src directory
```

#### Runtime Errors

```bash
# Problem: WebSocket connection failed
Solution: Check if port 8765 is available: lsof -i :8765

# Problem: Workflow stuck
Solution: dpo cancel <workflow_id>

# Problem: Out of memory
Solution: Reduce max_parallel_agents in configuration
```

### Debug Mode

```bash
# Enable debug logging
export DPO_LOG_LEVEL=DEBUG

# Run with verbose output
dpo build "test" -vvv

# Check detailed status
dpo status --detailed --workflow-id <id>
```

### Recovery Procedures

```bash
# Recover from checkpoint
dpo resume <checkpoint_file>

# Reset system state
rm -rf ~/.dpo/state/*
dpo configure --reset

# Rebuild from scratch
make clean
make deploy
```

## Security Considerations

### Access Control

```bash
# Restrict file permissions
chmod 600 ~/.dpo/config/*.json
chmod 700 ~/.dpo/bin/*

# Use API keys (when enabled)
export DPO_API_KEY="your-secure-key"
```

### Network Security

```bash
# Bind to localhost only
dpo server --host 127.0.0.1

# Enable SSL (requires certificates)
dpo server --ssl-cert cert.pem --ssl-key key.pem
```

### Sensitive Data

- Never commit credentials to version control
- Use environment variables for secrets
- Encrypt sensitive templates
- Regular security audits

### Compliance

```bash
# Enable audit logging
dpo configure --enable-audit-log

# Generate compliance report
dpo audit --format pdf > compliance_report.pdf
```

## Performance Optimization

### System Tuning

```bash
# Increase parallel agents for better performance
dpo configure --max-agents 20

# Optimize checkpoint frequency
dpo configure --checkpoint-interval 600

# Enable caching
dpo configure --enable-cache
```

### Resource Management

```bash
# Monitor resource usage
htop
iotop

# Limit memory usage
ulimit -v 8388608  # 8GB limit

# CPU affinity
taskset -c 0-7 dpo server  # Use cores 0-7
```

## Production Deployment

### Systemd Service

```ini
# /etc/systemd/system/dpo.service
[Unit]
Description=DPO System Service
After=network.target

[Service]
Type=simple
User=opsvi
WorkingDirectory=/home/opsvi/master_root/apps/dpo
ExecStart=/home/opsvi/.dpo/venv/bin/dpo server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable dpo
sudo systemctl start dpo
sudo systemctl status dpo
```

### Load Balancing

```nginx
# nginx.conf for multiple DPO instances
upstream dpo_servers {
    server localhost:8765;
    server localhost:8766;
    server localhost:8767;
}

server {
    listen 80;
    location /ws {
        proxy_pass http://dpo_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Support and Resources

### Documentation

- Main README: `/home/opsvi/master_root/apps/dpo/README.md`
- API Reference: `/home/opsvi/master_root/apps/dpo/docs/API_REFERENCE.md`
- Template Guide: `/home/opsvi/master_root/apps/dpo/docs/TEMPLATE_GUIDE.md`

### Logs and Diagnostics

```bash
# Generate diagnostic report
dpo diagnose > diagnostic_report.txt

# Collect logs for support
tar czf dpo_logs.tar.gz ~/.dpo/logs/
```

### Community

- GitHub Issues: Report bugs and request features
- Discord: Join the community chat
- Documentation: Check the docs/ directory

---

**Version**: 1.0.0
**Last Updated**: September 2025
**Deployment Package**: Complete
