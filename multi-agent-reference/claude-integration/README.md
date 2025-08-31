# Claude Integration Reference

This directory contains Claude-specific commands, workflows, and scripts that support multi-agent orchestration.

## Key Files

### SDLC Commands
- **sdlc.md** - Core SDLC command system (Discovery → Design → Planning → Development → Testing → Deployment → Production)
- **sdlc-execute-phase.py** - Python executor for SDLC phases
- **sdlc-phase-executor.sh** - Shell script for phase execution
- **sdlc-phase-executor-v2.py** - Enhanced phase executor with better error handling
- **sdlc-preflight.sh** / **sdlc-preflight-enhanced.sh** - Pre-execution checks
- **sdlc-postmortem.sh** - Post-execution analysis and learning
- **sdlc-gates.md** - Quality gates and checkpoints
- **sdlc-violation-analyzer.py** - Analyze and report violations
- **sdlc-task-enforcer.md** - Task enforcement rules

### Team Orchestration
- **team-orchestrate.py** - Main team orchestration command
  - Creates agent teams for different project types
  - Manages workflow execution across teams
  - Tracks project status

### Smart Commands (sc-*)
- **sc-01_brainstorm-feature.md** - Feature brainstorming workflow
- **sc-02_feature-proposal.md** - Feature proposal generation
- **sc-03_feature-to-prd.md** - Convert feature to PRD
- **sc-04_feature-planning.md** - Detailed feature planning
- **sc-05_implement.md** / **sc-05_implement_v2.md** - Implementation workflows
- **sc-mode-*.md** - Different operational modes (init, baseline, test, update)

### Workflows
- **app_development.yaml** - Application development workflow template
- **project_reorganization.yaml** - Project restructuring workflow
- **system_design.yaml** - System design workflow template

### Supporting Scripts
- **enhance-agent-profiles.py** - Script to enhance agent profiles with capabilities

## Integration Points

### 1. SDLC Phase Management
The SDLC commands provide a complete framework for managing development phases:
```bash
# Execute a specific phase
./sdlc-execute-phase.py --phase development --project my-project

# Run preflight checks
./sdlc-preflight-enhanced.sh

# Analyze violations
python sdlc-violation-analyzer.py --session current
```

### 2. Team Orchestration
The team-orchestrate command manages multi-agent teams:
```python
# From team-orchestrate.py
orchestrator = AgentTeamOrchestrator()
await orchestrator.create_team("my-project", ProjectType.WEB_APP)
await orchestrator.execute_workflow("my-project", phases=["design", "development"])
```

### 3. Smart Commands
Smart commands provide pre-built workflows for common tasks:
```markdown
# Feature development flow
1. /sc-01_brainstorm-feature - Generate ideas
2. /sc-02_feature-proposal - Create proposal
3. /sc-03_feature-to-prd - Convert to PRD
4. /sc-04_feature-planning - Plan implementation
5. /sc-05_implement - Execute implementation
```

## Key Patterns to Adopt

### 1. Phase-Based Execution
- Break work into clear phases (Discovery → Design → Development → Testing → Deployment)
- Use quality gates between phases
- Maintain phase-specific context and artifacts

### 2. Team Templates
From team-orchestrate.py:
- Different team compositions for different project types
- Role-based agent assignment
- Workflow templates per project type

### 3. Violation Analysis
From sdlc-violation-analyzer.py:
- Track and analyze violations
- Generate improvement recommendations
- Learn from past executions

### 4. Smart Command Patterns
- Progressive refinement (brainstorm → proposal → PRD → implementation)
- Mode-based operation (init, baseline, test, update)
- Built-in validation and testing

## Usage in Multi-Agent Design

### Adopt These Patterns:
1. **SDLC Phase Structure** - Clear phases with gates
2. **Team Templates** - Pre-defined team compositions
3. **Smart Command Workflows** - Progressive task refinement
4. **Violation Tracking** - Learning from errors

### Consider These Features:
1. **Preflight Checks** - Validate before execution
2. **Postmortem Analysis** - Learn from executions
3. **Mode-Based Operation** - Different modes for different contexts

### Integration Example:
```python
# Combining SDLC phases with multi-agent orchestration
class MultiAgentSDLC:
    def __init__(self):
        self.phases = ["discovery", "design", "planning", "development", "testing", "deployment"]
        self.team_orchestrator = AgentTeamOrchestrator()

    async def execute_project(self, project_name: str, project_type: str):
        # Create team based on project type
        await self.team_orchestrator.create_team(project_name, project_type)

        # Execute phases with gates
        for phase in self.phases:
            # Preflight checks
            if not self.run_preflight(phase):
                break

            # Execute phase
            result = await self.execute_phase(phase, project_name)

            # Quality gate
            if not self.check_gate(phase, result):
                break

            # Postmortem
            self.run_postmortem(phase, result)
```

## Notes
- These commands are designed for Claude-specific workflows
- Many assume specific directory structures and tool availability
- Adapt patterns rather than copying implementations directly
