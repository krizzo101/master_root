# SDLC Artifact Gates - Mandatory Checkpoints

## Purpose
Enforce SDLC phase progression through required artifacts. Each phase MUST create specific files before the next phase can begin.

## Implementation

### Phase Initialization
```bash
# At project start, create gate tracking
mkdir -p apps/<project-name>/.sdlc
echo '{"phase": "discovery", "project": "<project-name>", "started": "$(date -Iseconds)"}' > apps/<project-name>/.sdlc/state.json
```

### Required Artifacts by Phase

#### 1. DISCOVERY Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/discovery-complete.json
# Must contain:
{
  "requirements_doc": "docs/1-requirements.md",
  "existing_solutions_checked": true,
  "resource_discovery_results": [...],
  "knowledge_query_results": [...],
  "decision": "build_new|use_existing|extend_existing",
  "justification": "..."
}
```

**Gate Check:**
```bash
# Before proceeding to DESIGN
if [ ! -f "apps/<project-name>/.sdlc/discovery-complete.json" ]; then
  echo "ERROR: Cannot proceed to DESIGN without discovery artifacts"
  exit 1
fi
```

#### 2. DESIGN Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/design-complete.json
# Must contain:
{
  "design_doc": "docs/2-design.md",
  "architecture_diagram": true,
  "api_specifications": true,
  "data_models_defined": true,
  "technology_stack": {...}
}
```

#### 3. PLANNING Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/planning-complete.json
# Must contain:
{
  "planning_doc": "docs/3-planning.md",
  "task_count": 25,
  "task_ids": ["SETUP-1", "SETUP-2", ...],
  "total_effort_hours": 8.5,
  "dependencies_mapped": true,
  "todo_list_created": true,
  "todo_list_id": "project-<name>-tasks"
}
```

#### 4. DEVELOPMENT Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/development-complete.json
# Must contain:
{
  "tasks_completed": ["SETUP-1", "SETUP-2", ...],
  "commits": ["hash1", "hash2", ...],
  "files_created": 45,
  "tests_written": true,
  "lint_passing": true
}
```

#### 5. TESTING Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/testing-complete.json
# Must contain:
{
  "test_files": ["test_*.py"],
  "coverage_percent": 85,
  "tests_passing": 42,
  "tests_failing": 0,
  "integration_tests": true,
  "e2e_tests": true
}
```

#### 6. DEPLOYMENT Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/deployment-complete.json
# Must contain:
{
  "deployment_config": "deployment.yaml",
  "docker_image": "...",
  "ci_cd_configured": true,
  "monitoring_setup": true,
  "documentation_complete": true
}
```

#### 7. PRODUCTION Phase
**Required Outputs:**
```bash
apps/<project-name>/.sdlc/production-complete.json
# Must contain:
{
  "final_review": true,
  "knowledge_captured": true,
  "handover_complete": true,
  "lessons_learned": "..."
}
```

## Enforcement Script

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def check_phase_gate(project_path: Path, phase: str) -> bool:
    """Check if phase gate requirements are met."""
    gate_file = project_path / ".sdlc" / f"{phase}-complete.json"
    
    if not gate_file.exists():
        print(f"❌ Missing gate file: {gate_file}")
        return False
    
    with open(gate_file) as f:
        gate_data = json.load(f)
    
    # Validate required fields based on phase
    required_fields = {
        "discovery": ["requirements_doc", "existing_solutions_checked", "decision"],
        "design": ["design_doc", "architecture_diagram", "api_specifications"],
        "planning": ["planning_doc", "task_count", "task_ids", "todo_list_created"],
        "development": ["tasks_completed", "commits", "tests_written"],
        "testing": ["test_files", "coverage_percent", "tests_passing"],
        "deployment": ["deployment_config", "documentation_complete"],
        "production": ["final_review", "knowledge_captured"]
    }
    
    for field in required_fields.get(phase, []):
        if field not in gate_data:
            print(f"❌ Missing required field: {field}")
            return False
    
    print(f"✅ Phase {phase} gate requirements met")
    return True

if __name__ == "__main__":
    project = Path(sys.argv[1])
    phase = sys.argv[2]
    if not check_phase_gate(project, phase):
        sys.exit(1)
```

## Usage in SDLC Flow

```bash
# 1. Complete discovery work
# 2. Create gate artifact
echo '{
  "requirements_doc": "docs/1-requirements.md",
  "existing_solutions_checked": true,
  "resource_discovery_results": [...],
  "knowledge_query_results": [...],
  "decision": "build_new",
  "justification": "No existing solution meets requirements"
}' > apps/<project>/.sdlc/discovery-complete.json

# 3. Validate gate before proceeding
python .claude/commands/check_sdlc_gate.py apps/<project> discovery

# 4. Only if validation passes, proceed to next phase
```