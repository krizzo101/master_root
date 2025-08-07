# ACCF Project Map Structure Documentation

## Overview
This document memorializes the structure and content of the ACCF project map (`/home/opsvi/master_root/testing/ACCF/src/.proj-intel/project_map.yaml`) that the auto-attach script uses to find related files.

## Project Map Structure

### Top-Level Keys
```yaml
project_name: "src"
base_path: "/home/opsvi/master_root/testing/ACCF/src"
generated_at: "2025-08-07T13:05:56+00:00"
project_structure: {...}
entry_points: {...}
statistics: {...}
dependency_analysis: {...}
workflow_analysis: {...}
files: [...]
```

### 1. Project Structure Section
**Location**: `project_structure`
**Purpose**: File organization and type distribution

#### Available Information:
- **File Type Distribution**:
  - `python_files`: Count of Python files
  - `config_files`: Count of configuration files
  - `total_files`: Total file count

- **Module Structure**:
  - Organized by module (e.g., `accf`, `eda`)
  - Each module contains:
    - `files`: List of file paths in the module
    - `total_lines`: Total lines of code
    - `total_functions`: Number of functions
    - `total_classes`: Number of classes

### 2. Entry Points Section
**Location**: `entry_points`
**Purpose**: Application entry points and CLI interface

#### Available Information:
- **CLI Entry Points**:
  - `file`: Path to CLI file
  - `type`: Type of entry point (e.g., "command_line_interface")
  - `main_functions`: List of main functions
  - `cli_options`: CLI options and flags
  - `workflow_triggers`: Workflow trigger information

- **Core Entry Points**:
  - `file`: Path to core processor file
  - `type`: Type (e.g., "core_processor")
  - `main_functions`: List of main functions
  - `description`: Description of the entry point

### 3. Statistics Section
**Location**: `statistics`
**Purpose**: Overall code metrics and statistics

#### Available Information:
- `total_functions`: Total number of functions
- `total_classes`: Total number of classes
- `total_imports`: Total number of imports
- `total_lines`: Total lines of code
- `external_dependencies`: List of external dependencies

### 4. Dependency Analysis Section
**Location**: `dependency_analysis`
**Purpose**: Import relationships and dependency mapping

#### Available Information:
- **Most Imported Files**:
  - `file_path`: Path to the file
  - `imported_by_count`: Number of files that import this file
  - `imported_by`: List of files that import this file

- **Circular Dependencies**:
  - `cycle`: List of files in circular dependency
  - `severity`: Severity level (e.g., "high")

### 5. Workflow Analysis Section
**Location**: `workflow_analysis`
**Purpose**: Execution paths and workflow diagrams

#### Available Information:
- `workflow_paths`: Workflow execution paths
- `conditional_branches`: Conditional logic branches
- `function_calls`: Function call relationships
- `workflow_diagram`: Mermaid diagram of workflows

### 6. Files Section
**Location**: `files` (Array)
**Purpose**: Detailed analysis of each file in the project

#### File Entry Structure:
```yaml
- path: "file/path/here.py"
  line_count: 123
  filemap: "JSON string containing detailed file analysis"
```

#### Filemap JSON Structure:
The `filemap` field contains a JSON string with:

- **File Metadata**:
  - `type`: File type (e.g., "python")
  - `language`: Programming language
  - `title`: File title
  - `description`: File description
  - `last_updated`: Last update timestamp

- **Code Elements**:
  - `functions`: Array of function information
    - `name`: Function name
    - `line`: Line number
    - `parameters`: Function parameters
    - `is_async`: Whether function is async
    - `description`: Function description
    - `signature`: Function signature
    - `return_type`: Return type (if available)
  - `classes`: Array of class information
    - `name`: Class name
    - `line`: Line number
    - `inherits_from`: Parent classes
    - `methods`: Array of method information
    - `properties`: Array of property information
    - `description`: Class description
  - `imports`: Array of import information
    - `module`: Module name
    - `alias`: Import alias (if any)
    - `line`: Line number
    - `statement`: Full import statement
  - `constants`: Array of constant information

- **Key Elements**:
  - Array of important code elements with type and line number

- **Sections**:
  - `name`: Section name
  - `description`: Section description
  - `line_start`: Starting line number
  - `line_end`: Ending line number

- **Content Hash**:
  - `content_hash`: MD5 hash of file content

## Auto-Attach Script Usage

### What the Script Can Find:

1. **Import Dependencies**:
   - Files that import the user's file (from `imported_by` in dependency analysis)
   - Files that the user's file imports (from `imports` in filemap)

2. **Same Directory Files**:
   - Files in the same directory as the user's file
   - Found by comparing directory paths

3. **Configuration Files**:
   - package.json, requirements.txt, pyproject.toml
   - tsconfig.json, webpack.config.js, vite.config.js
   - jest.config.js, pytest.ini, .env files

4. **Test Files**:
   - Files with .test, _test, .spec extensions
   - Found by pattern matching on file names

5. **Type Definition Files**:
   - .d.ts files for TypeScript files
   - Found by pattern matching

### Script Processing Logic:

1. **File Lookup**: Find the user's file in the `files` array
2. **Import Analysis**: Parse the `filemap` JSON to extract imports
3. **Dependency Analysis**: Use `dependency_analysis` to find files that import the user's file
4. **Directory Scanning**: Find files in the same directory
5. **Pattern Matching**: Find related files by name patterns
6. **Configuration Detection**: Find configuration files in the same directory

### Example Usage:
```python
# User submits: "accf/orchestrator/mcp_agent_server.py"
# Script finds:
# - Files that import mcp_agent_server.py (from dependency_analysis)
# - Files that mcp_agent_server.py imports (from filemap imports)
# - Files in accf/orchestrator/ directory
# - Configuration files in accf/orchestrator/
# - Test files for mcp_agent_server.py
```

## Key Insights for Auto-Attach Script:

1. **Files are in a list, not a dictionary** - need to iterate to find matches
2. **Import information is in the filemap JSON** - need to parse JSON string
3. **Dependency analysis provides reverse imports** - files that import the target
4. **File paths are relative to base_path** - need to handle path resolution
5. **Rich metadata available** - can use for intelligent filtering
6. **Content hashes available** - can use for change detection

## Limitations:

1. **No direct "imported_by" in filemap** - only in dependency_analysis
2. **JSON parsing required** - filemap is a JSON string, not object
3. **Path resolution needed** - paths are relative to base_path
4. **No explicit file relationships** - need to infer from imports and directory structure
5. **Limited to analyzed files** - only files in the project map are available

This structure provides comprehensive information for intelligent file dependency analysis and auto-attachment functionality.
