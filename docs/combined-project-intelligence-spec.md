# Combined Project Intelligence Specification

## Overview

This document specifies the format and content for a combined project intelligence file that merges the current `project_map.yaml` and `project_analysis.json` files into a single, comprehensive format optimized for agent consumption.

## Purpose

The combined project intelligence file provides agents with a complete, integrated view of a project including:
- Project purpose and context
- File organization and relationships
- Agent architecture and capabilities
- Development state and constraints
- Technology stack and dependencies
- Entry points and APIs

## File Format

**Format**: YAML (for human readability and agent consumption)
**Filename**: `project_intelligence.yaml`
**Location**: `.proj-intel/project_intelligence.yaml`

## Structure Specification

### 1. Project Overview Section

```yaml
project:
  name: string                    # Project name (e.g., "ACCF")
  description: string             # High-level project description
  purpose: string                 # What the project does
  main_components: [string]       # Key components/modules
  technology_stack:
    languages: [string]           # Programming languages used
    frameworks: [string]          # Frameworks and libraries
    databases: [string]           # Database technologies
    external_apis: [string]       # External API integrations
    tools: [string]               # Development and analysis tools
  architecture:
    pattern: string               # Architecture pattern (e.g., "Multi-Agent System")
    communication: string         # Communication pattern
    data_flow: string             # Data flow description
    deployment: string            # Deployment approach
```

### 2. Development State Section

```yaml
development:
  git_repository: boolean         # Whether this is a git repository
  current_branch: string          # Current git branch
  remote_url: string              # Git remote URL
  active_branches: [string]       # List of active branches
  has_uncommitted_changes: boolean
  staged_files_count: integer
  unstaged_files_count: integer
  untracked_files_count: integer
  recent_activity:
    last_commit_days_ago: integer
    commits_last_week: integer
    commits_last_month: integer
    active_contributors: integer
  ci_status:
    has_ci: boolean
    ci_provider: string
    last_build_status: string
    last_build_time: string
  workflow:
    branching_strategy: string
    coding_standards: object
    development_process: object
    workflow_maturity: string
```

### 3. Constraints and Limitations Section

```yaml
constraints:
  technical_constraints:
    performance_constraints: [string]
    security_constraints: [string]
    scalability_constraints: [string]
    compatibility_constraints: [string]
    resource_constraints: [string]
    dependency_constraints: [string]
  business_rules:
    validation_rules: [string]
    business_logic: [string]
    compliance_requirements: [string]
  limitations:
    known_issues: [string]
    performance_limitations: [string]
    feature_limitations: [string]
    compatibility_limitations: [string]
    scalability_limitations: [string]
  constraint_summary:
    total_constraints: integer
    constraint_types: [string]
    critical_constraints: [string]
    constraint_impact: string
```

### 4. Agent Architecture Section

```yaml
agents:
  count: integer                  # Total number of agents
  types: [string]                 # Agent type categories
  communication:
    has_messaging: boolean
    has_event_system: boolean
    has_rpc: boolean
    has_grpc: boolean
    has_websockets: boolean
    has_queues: boolean
    protocols: [string]
  orchestration:
    has_orchestrator: boolean
    has_scheduler: boolean
    has_workflow: boolean
    has_task_queue: boolean
    orchestration_pattern: string
    coordination_mechanism: string
  configuration:
    has_agent_config: boolean
    config_files: [string]
    agent_settings: object
    environment_variables: [string]
  architecture_pattern: string
  has_multi_agent_system: boolean
  agent_list:
    - name: string                # Agent class name
      file_path: string           # File containing the agent
      lineno: integer             # Line number where agent is defined
      bases: [string]             # Parent classes
      agent_type: string          # Type of agent
      docstring: string           # Agent description
      purpose: string             # What this agent does
      capabilities: [string]      # What tasks it can handle
      methods:
        - name: string
          lineno: integer
          docstring: string
          purpose: string
```

### 5. File Structure Section

```yaml
files:
  "file/path/here.py":
    line_count: integer
    file_type: string             # "source", "config", "test", "documentation"
    category: string              # "agent_orchestration", "api", "core", "utils"
    purpose: string               # What this file does
    agent_related: boolean        # Whether this file is part of agent system
    critical: boolean             # Whether this is a critical file
    directory: string             # Directory containing the file
    imports: [string]             # What this file imports (processed)
    imported_by: [string]         # What files import this (processed)
    functions:
      - name: string
        lineno: integer
        docstring: string
        purpose: string
        is_async: boolean
    classes:
      - name: string
        lineno: integer
        docstring: string
        purpose: string
        bases: [string]
        methods: [object]
    constants: [object]
    sections:
      - name: string
        description: string
        line_start: integer
        line_end: integer
```

### 6. Entry Points and APIs Section

```yaml
entry_points:
  cli:
    file: string
    type: string
    main_functions: [string]
    cli_options: object
    workflow_triggers: [string]
  core:
    file: string
    type: string
    main_functions: [string]
    description: string
  apis:
    mcp_endpoints:
      - name: string
        description: string
        parameters: [object]
    rest_endpoints:
      - path: string
        method: string
        description: string
        parameters: [object]
    websocket_endpoints:
      - path: string
        description: string
```

### 7. Statistics Section

```yaml
statistics:
  total_agents: integer
  total_files: integer
  total_functions: integer
  total_classes: integer
  total_imports: integer
  total_lines: integer
  file_type_distribution:
    source_files: integer
    config_files: integer
    test_files: integer
    documentation_files: integer
  module_distribution:
    module_name:
      files: [string]
      total_lines: integer
      total_functions: integer
      total_classes: integer
```

### 8. Indexes Section

```yaml
indexes:
  by_directory:
    "directory/path": [string]    # List of files in directory
  by_import:
    "module.name": [string]       # Files that import this module
  by_type:
    source: [string]              # Source files
    config: [string]              # Configuration files
    test: [string]                # Test files
    documentation: [string]       # Documentation files
  by_category:
    agent_orchestration: [string] # Agent-related files
    api: [string]                 # API files
    core: [string]                # Core functionality files
    utils: [string]               # Utility files
  agent_files: [string]           # Files that are part of agent system
  critical_files: [string]        # Critical system files
  entry_point_files: [string]     # Files that serve as entry points
```

### 9. Dependencies Section

```yaml
dependencies:
  external:
    - name: string
      version: string
      purpose: string
      critical: boolean
  internal:
    circular_dependencies:
      - cycle: [string]
        severity: string
    most_imported_files:
      - file_path: string
        imported_by_count: integer
        imported_by: [string]
  dependency_graph:
    nodes: [string]               # File paths
    edges: [object]               # Import relationships
```

### 10. Metadata Section

```yaml
metadata:
  generated_at: string            # ISO timestamp
  generator_version: string       # Version of generator tool
  schema_version: string          # Schema version
  base_path: string               # Project base path
  file_size: integer              # Size of generated file
  generation_time_ms: integer     # Time taken to generate
```

## Content Requirements

### Required Fields
- `project.name`
- `project.description`
- `files` (at least one file)
- `metadata.generated_at`
- `metadata.schema_version`

### Optional Fields
- All other fields are optional but recommended for comprehensive project intelligence

### Data Quality Requirements
- File paths must be relative to project base path
- Import relationships must be processed and normalized
- Agent information must be accurate and up-to-date
- Statistics must be calculated correctly
- Indexes must be complete and accurate

## Generation Process

### Input Sources
1. **Project Map Data**: File structure, imports, code elements
2. **Project Analysis Data**: Development state, constraints, agent architecture
3. **Git Information**: Repository state, branches, activity
4. **File System**: Directory structure, file types, sizes

### Processing Steps
1. **Parse existing files**: Extract data from current project_map.yaml and project_analysis.json
2. **Analyze file relationships**: Process import statements and build dependency graph
3. **Classify files**: Determine file types, categories, and purposes
4. **Integrate agent data**: Map agents to files and capabilities
5. **Build indexes**: Create fast-lookup indexes for common queries
6. **Validate data**: Ensure consistency and completeness
7. **Generate output**: Create the combined YAML file

### Validation Rules
- All file paths must exist in the project
- Import relationships must be bidirectional consistent
- Agent file paths must point to actual files
- Statistics must match actual file counts
- Indexes must contain valid file references

## Usage Guidelines

### For Agents
- Use the `project` section for high-level understanding
- Use the `agents` section to understand available capabilities
- Use the `files` section for detailed file analysis
- Use the `indexes` section for fast lookups
- Use the `dependencies` section for relationship analysis

### For Tools
- Use the `indexes` section for programmatic access
- Use the `statistics` section for metrics and reporting
- Use the `dependencies` section for impact analysis
- Use the `metadata` section for version and generation info

## Migration Strategy

### Phase 1: Generate Combined File
- Create new generator that combines existing data
- Maintain backward compatibility with existing files
- Generate both old and new formats during transition

### Phase 2: Update Tools
- Update agents to use new combined format
- Update scripts to use new indexes
- Update documentation and examples

### Phase 3: Deprecate Old Formats
- Mark old files as deprecated
- Remove old format generation
- Update all references to use new format

## Example Output

```yaml
project:
  name: "ACCF"
  description: "AI/ML Operations platform with multi-agent system"
  purpose: "Provides intelligent agents for technical research, documentation, and code generation"
  main_components: ["Research Agents", "Documentation Agents", "Code Review Agents"]
  technology_stack:
    languages: ["Python"]
    frameworks: ["FastAPI", "Pydantic", "SQLAlchemy"]
    databases: ["Neo4j", "SQLite"]
    external_apis: ["OpenAI", "Brave Search", "Firecrawl"]

development:
  git_repository: true
  current_branch: "refactor/coding_agent_2025Q3"
  has_uncommitted_changes: true
  recent_activity:
    last_commit_days_ago: 0
    commits_last_week: 50

agents:
  count: 143
  types: ["analyzer", "collector", "orchestrator", "general", "assistant"]
  agent_list:
    - name: "ConsultAgent"
      file_path: "accf/agents/consult_agent_comprehensive.py"
      agent_type: "assistant"
      purpose: "Provides intelligent consultation for development tasks"
      capabilities: ["code_review", "documentation", "research"]

files:
  "accf/orchestrator/mcp_agent_server.py":
    line_count: 2933
    file_type: "source"
    category: "agent_orchestration"
    purpose: "MCP server for agent communication"
    agent_related: true
    critical: true
    imports: ["accf.agents.challenge_agent", "accf.agents.consult_agent_comprehensive"]
    imported_by: []
    functions:
      - name: "main"
        lineno: 22
        purpose: "Entry point for MCP server"
        is_async: false

indexes:
  by_directory:
    "accf/orchestrator": ["mcp_agent_server.py", "core.py", "task_market.py"]
  by_import:
    "accf.agents.challenge_agent": ["accf/orchestrator/mcp_agent_server.py"]
  agent_files: ["accf/agents/consult_agent_comprehensive.py", "accf/orchestrator/mcp_agent_server.py"]

metadata:
  generated_at: "2025-08-07T13:05:58.123456"
  schema_version: "1.0.0"
  base_path: "/home/opsvi/master_root/testing/ACCF/src"
```

This specification provides a comprehensive, agent-optimized format that combines all necessary project intelligence into a single, easily consumable file.
