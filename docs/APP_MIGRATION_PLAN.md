# App Migration and Refactoring Plan

## Executive Summary

This document outlines the plan to migrate and refactor `proj-mapper` and `auto-forge-factory` applications to fully integrate with the master_root project's shared libraries and infrastructure, with the primary goal of replacing custom agents with the claude-code agent.

## Current State Analysis

### proj-mapper
- **Purpose**: Maps and visualizes project structures and relationships
- **Size**: ~18 directories, moderate complexity
- **Dependencies**: pydantic, pyyaml, graphviz (optional)
- **Architecture**: Modular with analyzers, models, pipeline, storage
- **Current Issues**:
  - Has its own .venv (needs to use master_root venv)
  - Not using shared libs from master_root
  - Custom CLI implementation instead of shared patterns

### auto-forge-factory
- **Purpose**: Autonomous software development factory with multi-agent orchestration
- **Size**: Complex multi-agent system
- **Dependencies**: FastAPI, Redis, PostgreSQL, OpenAI/Anthropic APIs
- **Architecture**: 10+ specialized agents (Planner, Coder, Tester, etc.)
- **Current Issues**:
  - Heavy custom agent implementation (10+ agents)
  - Separate infrastructure requirements (Redis, PostgreSQL)
  - Not leveraging claude-code agent capabilities

## Migration Strategy

### Phase 1: proj-mapper Migration (Easier, Start Here)

#### 1.1 Dependency Analysis and Mapping
```
Current proj-mapper Components → Master Root Libs Mapping:

proj_mapper/core/               → libs/opsvi-core/
proj_mapper/models/             → libs/opsvi-models/
proj_mapper/storage/            → libs/opsvi-data/
proj_mapper/analyzers/          → libs/opsvi-agents/ (use claude-code)
proj_mapper/pipeline/           → libs/opsvi-pipeline/
proj_mapper/cli/                → libs/opsvi-interfaces/
proj_mapper/output/             → libs/opsvi-visualization/ (new)
proj_mapper/utils/              → libs/opsvi-utils/
```

#### 1.2 Implementation Steps

**Step 1: Create Missing Libraries**
```python
# Create libs/opsvi-visualization for output generation
libs/opsvi-visualization/
├── __init__.py
├── generators/
│   ├── dot.py
│   ├── html.py
│   └── svg.py
├── models/
│   └── visualization_types.py
└── utils/
    └── graph_utils.py
```

**Step 2: Refactor Core Components**
- Replace `proj_mapper.core.project_manager` with `opsvi_orchestration.ProjectOrchestrator`
- Use `opsvi_data.storage.FileStorage` instead of custom storage
- Migrate models to use `opsvi_models.base.BaseModel`

**Step 3: Replace Analyzers with Claude-Code Agent**
```python
# Before (custom analyzer):
from proj_mapper.analyzers.code_analyzer import CodeAnalyzer
analyzer = CodeAnalyzer()
result = analyzer.analyze(file_path)

# After (claude-code agent):
from opsvi_agents.claude_code import ClaudeCodeAgent
agent = ClaudeCodeAgent()
result = await agent.analyze_code(file_path, task="map_structure")
```

**Step 4: Update CLI to Use Shared Interfaces**
```python
# Use opsvi-interfaces for CLI
from opsvi_interfaces.cli import BaseCLI, command
from opsvi_interfaces.config import ConfigManager

class ProjMapperCLI(BaseCLI):
    @command
    def analyze(self, project_path: str):
        # Implementation using shared libs
        pass
```

**Step 5: Integration Testing**
- Test with master_root's existing test infrastructure
- Ensure all functionality works with shared libs
- Validate visualization outputs

### Phase 2: auto-forge-factory Migration (Complex)

#### 2.1 Agent Consolidation Strategy

**Replace ALL specialized agents with claude-code agent profiles:**

```python
# Agent Mapping to Claude-Code Profiles
AGENT_PROFILES = {
    "planner": {
        "mode": "plan",
        "temperature": 0.1,
        "system_prompt": "You are a software planning specialist..."
    },
    "specifier": {
        "mode": "requirements",
        "temperature": 0.2,
        "system_prompt": "You are a requirements specification expert..."
    },
    "architect": {
        "mode": "design",
        "temperature": 0.3,
        "system_prompt": "You are a software architect..."
    },
    "coder": {
        "mode": "development",
        "temperature": 0.2,
        "system_prompt": "You are an expert programmer..."
    },
    "tester": {
        "mode": "testing",
        "temperature": 0.1,
        "system_prompt": "You are a QA engineer..."
    },
    "optimizer": {
        "mode": "optimize",
        "temperature": 0.2,
        "system_prompt": "You are a performance optimization expert..."
    },
    "security": {
        "mode": "security",
        "temperature": 0.1,
        "system_prompt": "You are a security expert..."
    },
    "critic": {
        "mode": "review",
        "temperature": 0.3,
        "system_prompt": "You are a code review expert..."
    }
}
```

#### 2.2 Infrastructure Simplification

**Replace complex infrastructure with master_root components:**
```
Current → Master Root Replacement:

Redis Cache        → libs/opsvi-memory (in-memory or file-based)
PostgreSQL         → libs/opsvi-data + Neo4j knowledge base
Custom Monitoring  → libs/opsvi-monitoring
WebSocket Updates  → libs/opsvi-communication
Job Management     → libs/opsvi-orchestration
```

#### 2.3 Implementation Steps

**Step 1: Create Unified Agent Orchestrator**
```python
# libs/opsvi-orchestration/software_factory.py
from opsvi_agents.claude_code import ClaudeCodeAgent
from opsvi_pipeline.pipeline import Pipeline

class SoftwareFactory:
    def __init__(self):
        self.agent = ClaudeCodeAgent()
        self.pipeline = Pipeline()

    async def develop(self, requirements: dict):
        # Orchestrate claude-code agent with different profiles
        plan = await self.agent.execute(requirements, profile="planner")
        spec = await self.agent.execute(plan, profile="specifier")
        design = await self.agent.execute(spec, profile="architect")
        code = await self.agent.execute(design, profile="coder")
        tests = await self.agent.execute(code, profile="tester")
        optimized = await self.agent.execute(code, profile="optimizer")
        return optimized
```

**Step 2: Migrate API Layer**
```python
# Use existing FastAPI patterns from libs
from opsvi_web.api import BaseAPI
from opsvi_interfaces.websocket import WebSocketManager

class AutoForgeAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.factory = SoftwareFactory()
        self.ws_manager = WebSocketManager()
```

**Step 3: Simplify Job Management**
```python
# Use opsvi-orchestration for job management
from opsvi_orchestration.job_manager import JobManager
from opsvi_data.storage import JobStorage

class FactoryJobManager(JobManager):
    def __init__(self):
        super().__init__(storage=JobStorage())
```

## Implementation Timeline

### Week 1-2: proj-mapper Migration
- Day 1-2: Create opsvi-visualization library
- Day 3-4: Refactor core components
- Day 5-6: Replace analyzers with claude-code
- Day 7-8: Update CLI and interfaces
- Day 9-10: Integration testing and fixes

### Week 3-4: auto-forge-factory Migration
- Day 1-3: Create agent profile system
- Day 4-6: Replace all agents with claude-code
- Day 7-9: Migrate infrastructure to shared libs
- Day 10-12: API and job management migration
- Day 13-14: End-to-end testing

## Benefits of Migration

1. **Code Reuse**: Eliminate duplicate code by using shared libraries
2. **Simplified Maintenance**: Single agent (claude-code) instead of 10+ custom agents
3. **Better Integration**: Native integration with master_root ecosystem
4. **Reduced Dependencies**: Use existing infrastructure instead of Redis/PostgreSQL
5. **Unified Testing**: Leverage master_root's test infrastructure
6. **Knowledge Sharing**: Use Neo4j knowledge base across all apps
7. **Consistent Patterns**: Follow master_root's established patterns

## Success Criteria

### For proj-mapper:
- [ ] All functionality works using shared libs
- [ ] No custom .venv, uses master_root environment
- [ ] Claude-code agent handles all analysis tasks
- [ ] Visualization generation works correctly
- [ ] Tests pass using shared test infrastructure

### For auto-forge-factory:
- [ ] All agents replaced with claude-code profiles
- [ ] No external infrastructure dependencies (Redis/PostgreSQL)
- [ ] API works with shared web framework
- [ ] Job management uses shared orchestration
- [ ] End-to-end software generation works

## Risk Mitigation

1. **Backup Strategy**: Keep original code in .archive during migration
2. **Incremental Migration**: Migrate one component at a time
3. **Feature Parity Testing**: Ensure all features work after migration
4. **Performance Monitoring**: Track performance impact of changes
5. **Rollback Plan**: Git branches for each migration phase

## Next Steps

1. **Start with proj-mapper** as the simpler migration
2. **Create missing shared libraries** (opsvi-visualization)
3. **Set up migration branches** in git
4. **Begin incremental refactoring** following the plan
5. **Document changes** and update README files

## Notes

- The claude-code agent is powerful enough to replace all specialized agents
- Using profiles and prompts, we can achieve the same specialization
- Shared libraries will make future app integrations much easier
- This migration will serve as a template for future app integrations
