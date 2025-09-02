# Apps Directory

This directory contains active applications that are ready for development and integration.

## Current Status

- **Active Applications**: 2 new orchestration tools
- **Git-tracked** - Changes here are committed to the main branch

## Workflow

1. **Staging**: New applications are added to `../intake/` (git-ignored)
2. **Review**: Applications are reviewed and prepared for integration
3. **Activation**: When ready, applications are moved from `intake/` to `apps/`
4. **Development**: Active development and integration work begins

## Structure

```
apps/
├── README.md                # This file
├── agent-orchestrator/      # Generic multi-agent orchestration framework
│   ├── src/                # Core orchestrator code
│   ├── tests/              # Test scripts
│   ├── docs/               # Documentation
│   └── examples/           # Usage examples
├── wbs-documenter/         # WBS documentation system for auto-coding
│   ├── src/                # WBS-specific implementation
│   ├── docs/               # Process documentation
│   ├── templates/          # Document templates
│   └── output/             # Generated documentation
├── hecaton/                # Multi-agent orchestration (LangGraph-based)
├── razer/                  # Code intelligence system
└── [other apps]/           # Additional applications

intake/                     # Staging area (git-ignored)
├── ACCF/                   # Staged for future integration
├── asea/                   # Staged for future integration
├── auto_forge/             # Staged for future integration
├── genFileMap/             # Staged for future integration
└── project-intelligence/   # Staged for future integration
```

## Active Applications

### 1. Agent Orchestrator (`agent-orchestrator/`)
**Generic framework for orchestrating parallel Claude agents**
- Token pool management
- Dependency resolution
- Message passing between agents
- 3-5 second execution with optimizations
- Reusable for any multi-agent use case

**Quick Start:**
```bash
cd agent-orchestrator
./run.py
```

### 2. WBS Documenter (`wbs-documenter/`)
**Adaptive documentation system using Work Breakdown Structure**
- Discovers structure through agent exploration
- Cascading documentation generation
- Human review checkpoints
- Built on agent-orchestrator framework

**Quick Start:**
```bash
cd wbs-documenter
./run.py
```

## Guidelines

- Keep `apps/` clean and focused on active development
- Use `intake/` for staging and preparation
- Commit changes immediately when moving apps from `intake/` to `apps/`
- Follow the established workflow to prevent confusion
