# Agent Orchestrator

A production-ready multi-agent orchestration framework for managing parallel Claude agents with advanced features including dependency management, token pooling, quality gates, and intelligent escalation systems.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the orchestrator
python main.py
```

## Core Orchestrators

- **Generic Orchestrator** (`src/generic_orchestrator.py`) - Current standard and base implementation
- **Enhanced Orchestrator** (`src/enhanced_orchestrator.py`) - Advanced features with configurable limitations  
- **Unified Orchestrator** (`src/unified/`) - New standard being validated and updated

## Directory Structure

```
agent-orchestrator/
├── src/                    # Core source code
├── examples/               # Example implementations
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── utils/                  # Utilities
├── archive/                # Archived files
├── requirements.txt        # Dependencies
├── setup.py               # Package setup
├── config.example.yaml    # Configuration template
├── main.py                # Entry point
└── run.py                 # Alternative entry point
```

## Features

- Parallel execution of multiple agents
- Smart dependency management
- Token pooling and resource management
- Quality gates and validation
- Escalation system for complex tasks
- Real-time monitoring and progress tracking

## Documentation

See the `docs/` directory for comprehensive documentation including API reference, architecture details, and tutorials.
