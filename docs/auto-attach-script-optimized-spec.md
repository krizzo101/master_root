# Auto-Attach Script Optimized File Specification

## Overview

This document specifies the format and content for a file optimized specifically for the auto-attach script functionality. This format is designed for maximum performance and minimal complexity, with no consideration for human readability or agent consumption.

## Purpose

The auto-attach script needs to:
1. Find files by path (O(1) lookup)
2. Find what files a given file imports
3. Find what files import a given file
4. Find files in the same directory
5. Find configuration and test files
6. Classify files by type

## File Format

**Format**: JSON (for maximum parsing speed)
**Filename**: `file_dependencies.json`
**Location**: `.proj-intel/file_dependencies.json`

## Structure Specification

### Core File Structure

```json
{
  "files": {
    "file/path/here.py": {
      "imports": ["module1", "module2"],
      "imported_by": ["file1.py", "file2.py"],
      "directory": "path/to/dir",
      "file_type": "source|config|test|documentation",
      "line_count": 123
    }
  },
  "indexes": {
    "by_directory": {
      "path/to/dir": ["file1.py", "file2.py", "file3.py"]
    },
    "by_import": {
      "module1": ["file1.py", "file2.py"],
      "module2": ["file3.py"]
    },
    "by_type": {
      "source": ["file1.py", "file2.py"],
      "config": ["config1.json", "config2.yaml"],
      "test": ["test1.py", "test2.py"],
      "documentation": ["readme.md", "docs.md"]
    }
  },
  "metadata": {
    "generated_at": "2025-08-07T13:05:58.123456",
    "total_files": 171,
    "base_path": "/home/opsvi/master_root/testing/ACCF/src"
  }
}
```

### Detailed Field Specifications

#### Files Object

```json
{
  "files": {
    "accf/orchestrator/mcp_agent_server.py": {
      "imports": [
        "accf.agents.challenge_agent",
        "accf.agents.consult_agent_comprehensive",
        "accf.agents.critique_agent",
        "accf.agents.documentation_agent",
        "accf.agents.documentation_bundle_agent",
        "accf.agents.error_capture_agent",
        "accf.agents.knowledge_agent",
        "accf.agents.memory_agent",
        "accf.agents.integrated_research_agent",
        "accf.agents.self_reflection_agent",
        "accf.agents.testing_agent",
        "accf.agents.coding_agent",
        "accf.agents.code_review_agent",
        "accf.agents.enhanced_documentation_agent",
        "accf.agents.enhanced_documentation_agent.core.request_schema",
        "accf.shared.mcp.mcp_server_template",
        "accf.shared.mcp.mcp_server_template",
        "accf.shared.mcp.mcp_server_template"
      ],
      "imported_by": [],
      "directory": "accf/orchestrator",
      "file_type": "source",
      "line_count": 2933
    }
  }
}
```

**Field Descriptions:**
- `imports`: Array of module names that this file imports (normalized, no duplicates)
- `imported_by`: Array of file paths that import this file
- `directory`: Directory containing this file (for fast directory queries)
- `file_type`: Classification of file type
- `line_count`: Number of lines in the file

#### Indexes Object

```json
{
  "indexes": {
    "by_directory": {
      "accf/orchestrator": [
        "accf/orchestrator/__init__.py",
        "accf/orchestrator/core.py",
        "accf/orchestrator/mcp_agent_server.py",
        "accf/orchestrator/task_market.py",
        "accf/orchestrator/subscription_engine.py"
      ],
      "accf/agents": [
        "accf/agents/__init__.py",
        "accf/agents/base.py",
        "accf/agents/challenge_agent.py",
        "accf/agents/consult_agent_comprehensive.py"
      ]
    },
    "by_import": {
      "accf.agents.challenge_agent": [
        "accf/orchestrator/mcp_agent_server.py"
      ],
      "accf.agents.consult_agent_comprehensive": [
        "accf/orchestrator/mcp_agent_server.py"
      ],
      "accf.utils.logging": [
        "accf/core/monitoring.py",
        "accf/core/neo4j_vector.py",
        "accf/core/model_selection_engine.py",
        "accf/core/neo4j_knowledge_graph.py",
        "accf/core/neo4j_integration.py",
        "accf/core/agent_base.py",
        "accf/core/orchestrator.py",
        "accf/core/intelligent_file_analyzer.py",
        "accf/core/registry.py",
        "accf/core/technical_knowledge_base.py",
        "accf/orchestrator/core.py",
        "accf/orchestrator/mcp_agent_server.py"
      ]
    },
    "by_type": {
      "source": [
        "accf/orchestrator/mcp_agent_server.py",
        "accf/agents/challenge_agent.py",
        "accf/core/monitoring.py"
      ],
      "config": [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        ".env"
      ],
      "test": [
        "test_mcp_agent_server.py",
        "test_challenge_agent.py",
        "test_monitoring.py"
      ],
      "documentation": [
        "README.md",
        "docs/api.md",
        "docs/architecture.md"
      ]
    }
  }
}
```

**Index Descriptions:**
- `by_directory`: Maps directory paths to arrays of files in that directory
- `by_import`: Maps module names to arrays of files that import that module
- `by_type`: Maps file types to arrays of files of that type

#### Metadata Object

```json
{
  "metadata": {
    "generated_at": "2025-08-07T13:05:58.123456",
    "total_files": 171,
    "base_path": "/home/opsvi/master_root/testing/ACCF/src",
    "schema_version": "1.0.0",
    "file_size_bytes": 45678,
    "generation_time_ms": 1234
  }
}
```

**Field Descriptions:**
- `generated_at`: ISO timestamp of when the file was generated
- `total_files`: Total number of files in the project
- `base_path`: Absolute path to the project root
- `schema_version`: Version of this schema
- `file_size_bytes`: Size of this JSON file in bytes
- `generation_time_ms`: Time taken to generate this file in milliseconds

## File Type Classification

### Source Files
- **Criteria**: Python files with `.py` extension that contain code
- **Examples**: `mcp_agent_server.py`, `challenge_agent.py`, `monitoring.py`

### Configuration Files
- **Criteria**: Files that configure the project or its dependencies
- **Examples**: `package.json`, `requirements.txt`, `pyproject.toml`, `setup.py`, `.env`, `config.py`, `settings.py`

### Test Files
- **Criteria**: Files that test other files
- **Patterns**:
  - `test_*.py`
  - `*_test.py`
  - `*Test.py`
  - `*_spec.py`
  - `*Spec.py`

### Documentation Files
- **Criteria**: Files that document the project
- **Examples**: `README.md`, `docs/*.md`, `*.rst`, `*.txt` (documentation)

## Import Processing Rules

### Module Name Normalization
1. **Remove file extensions**: `accf.agents.challenge_agent.py` → `accf.agents.challenge_agent`
2. **Handle relative imports**: `from . import module` → `current_package.module`
3. **Handle aliased imports**: `import module as alias` → `module`
4. **Handle from imports**: `from module import item` → `module`
5. **Remove duplicates**: Keep only unique module names

### Import Relationship Processing
1. **Bidirectional consistency**: If A imports B, then B is imported_by A
2. **Module to file mapping**: Map module names to actual file paths
3. **Handle missing files**: Skip imports that don't correspond to project files
4. **Normalize paths**: Use consistent path separators and relative paths

## Performance Optimizations

### Data Structure Choices
1. **Objects over arrays**: Use file paths as keys for O(1) lookup
2. **Pre-computed indexes**: Avoid runtime computation
3. **Minimal data**: Only include data needed by the script
4. **Normalized strings**: Avoid duplicate string storage

### Lookup Optimizations
1. **Direct file access**: `files[file_path]` for O(1) file lookup
2. **Directory queries**: `indexes.by_directory[directory]` for O(1) directory listing
3. **Import queries**: `indexes.by_import[module]` for O(1) import lookup
4. **Type queries**: `indexes.by_type[file_type]` for O(1) type filtering

## Generation Process

### Input Processing
1. **Parse project files**: Scan all files in the project
2. **Extract imports**: Parse import statements from each file
3. **Build relationships**: Create bidirectional import mappings
4. **Classify files**: Determine file types based on patterns
5. **Build indexes**: Create lookup tables for common queries
6. **Validate data**: Ensure consistency and completeness

### Output Generation
1. **Create files object**: Map file paths to file information
2. **Create indexes**: Build lookup tables for fast access
3. **Add metadata**: Include generation information
4. **Serialize to JSON**: Output optimized JSON format

## Usage by Auto-Attach Script

### File Lookup
```python
# O(1) file lookup
file_info = data["files"].get("accf/orchestrator/mcp_agent_server.py")
if file_info:
    imports = file_info["imports"]
    imported_by = file_info["imported_by"]
    directory = file_info["directory"]
    file_type = file_info["file_type"]
```

### Directory Queries
```python
# O(1) directory listing
same_dir_files = data["indexes"]["by_directory"].get("accf/orchestrator", [])
```

### Import Queries
```python
# O(1) import lookup
importers = data["indexes"]["by_import"].get("accf.agents.challenge_agent", [])
```

### Type Queries
```python
# O(1) type filtering
config_files = data["indexes"]["by_type"].get("config", [])
test_files = data["indexes"]["by_type"].get("test", [])
```

### Auto-Attach Algorithm
```python
def auto_attach_files(user_files):
    related_files = set(user_files)

    for user_file in user_files:
        file_info = data["files"].get(user_file)
        if file_info:
            # Add imported files
            for module in file_info["imports"]:
                importers = data["indexes"]["by_import"].get(module, [])
                related_files.update(importers)

            # Add files that import this file
            related_files.update(file_info["imported_by"])

            # Add files in same directory
            same_dir = data["indexes"]["by_directory"].get(file_info["directory"], [])
            related_files.update(same_dir)

            # Add config files in same directory
            config_files = data["indexes"]["by_type"].get("config", [])
            for config_file in config_files:
                if config_file.startswith(file_info["directory"]):
                    related_files.add(config_file)

    return list(related_files)
```

## Validation Rules

### Required Fields
- `files` object must exist and contain at least one file
- `indexes` object must exist with all required indexes
- `metadata` object must exist with required fields

### Data Consistency
- All file paths in indexes must exist in files object
- Import relationships must be bidirectional consistent
- Directory paths must be valid and consistent
- File types must be one of the defined types

### Performance Requirements
- File lookup must be O(1)
- Directory queries must be O(1)
- Import queries must be O(1)
- Type queries must be O(1)

## Example Output

```json
{
  "files": {
    "accf/orchestrator/mcp_agent_server.py": {
      "imports": [
        "accf.agents.challenge_agent",
        "accf.agents.consult_agent_comprehensive",
        "accf.agents.critique_agent",
        "accf.agents.documentation_agent",
        "accf.agents.documentation_bundle_agent",
        "accf.agents.error_capture_agent",
        "accf.agents.knowledge_agent",
        "accf.agents.memory_agent",
        "accf.agents.integrated_research_agent",
        "accf.agents.self_reflection_agent",
        "accf.agents.testing_agent",
        "accf.agents.coding_agent",
        "accf.agents.code_review_agent",
        "accf.agents.enhanced_documentation_agent",
        "accf.agents.enhanced_documentation_agent.core.request_schema",
        "accf.shared.mcp.mcp_server_template"
      ],
      "imported_by": [],
      "directory": "accf/orchestrator",
      "file_type": "source",
      "line_count": 2933
    },
    "accf/agents/challenge_agent.py": {
      "imports": [],
      "imported_by": ["accf/orchestrator/mcp_agent_server.py"],
      "directory": "accf/agents",
      "file_type": "source",
      "line_count": 150
    }
  },
  "indexes": {
    "by_directory": {
      "accf/orchestrator": [
        "accf/orchestrator/__init__.py",
        "accf/orchestrator/core.py",
        "accf/orchestrator/mcp_agent_server.py",
        "accf/orchestrator/task_market.py",
        "accf/orchestrator/subscription_engine.py"
      ],
      "accf/agents": [
        "accf/agents/__init__.py",
        "accf/agents/base.py",
        "accf/agents/challenge_agent.py",
        "accf/agents/consult_agent_comprehensive.py"
      ]
    },
    "by_import": {
      "accf.agents.challenge_agent": ["accf/orchestrator/mcp_agent_server.py"],
      "accf.agents.consult_agent_comprehensive": ["accf/orchestrator/mcp_agent_server.py"]
    },
    "by_type": {
      "source": [
        "accf/orchestrator/mcp_agent_server.py",
        "accf/agents/challenge_agent.py",
        "accf/agents/consult_agent_comprehensive.py"
      ],
      "config": ["package.json", "requirements.txt"],
      "test": ["test_mcp_agent_server.py"],
      "documentation": ["README.md"]
    }
  },
  "metadata": {
    "generated_at": "2025-08-07T13:05:58.123456",
    "total_files": 171,
    "base_path": "/home/opsvi/master_root/testing/ACCF/src",
    "schema_version": "1.0.0",
    "file_size_bytes": 45678,
    "generation_time_ms": 1234
  }
}
```

This specification provides a minimal, high-performance format optimized specifically for the auto-attach script's needs with no consideration for human readability or other use cases.
