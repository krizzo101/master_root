# Interface Specifications

**Version:** 1.0.0  
**Last Updated:** 2023-11-05  
**Status:** Draft

## Document Purpose

This document specifies the interfaces for the Project Mapper system, including command-line interface, programmatic API, output formats, and integration points with VSCode-based IDEs like Cursor.

## Command Line Interface

### Command Structure

```
proj_mapper [options] command [command_options] [path]
```

Where:

- `options`: Global options for the command
- `command`: The command to execute
- `command_options`: Options specific to the command
- `path`: The path to the project directory (defaults to current directory)

### Global Options

| Option              | Description                                 | Default                            |
| ------------------- | ------------------------------------------- | ---------------------------------- |
| `--config FILE`     | Path to configuration file                  | `.proj_mapper.yml` in project root |
| `--log-level LEVEL` | Logging level (debug, info, warning, error) | `info`                             |
| `--output-dir DIR`  | Directory for output files                  | `.maps` in project root            |
| `--verbose`         | Enable verbose output                       | `false`                            |

### Commands

#### analyze

Analyze the project and generate maps

```
proj_mapper analyze [--map-types=TYPE1,TYPE2,...] [--include=PATTERN] [--exclude=PATTERN] [path]
```

| Option        | Description                                                                    | Default                        |
| ------------- | ------------------------------------------------------------------------------ | ------------------------------ |
| `--map-types` | Types of maps to generate (project, file, module, relationship, documentation) | `all`                          |
| `--include`   | Glob pattern for files to include                                              | `*.py,*.md`                    |
| `--exclude`   | Glob pattern for files to exclude                                              | `**/venv/**,**/__pycache__/**` |

#### update

Update existing maps with changes

```
proj_mapper update [--incremental] [path]
```

| Option          | Description                        | Default |
| --------------- | ---------------------------------- | ------- |
| `--incremental` | Only update maps for changed files | `true`  |

#### config

Manage configuration

```
proj_mapper config [get|set|list] [key] [value]
```

## Programmatic API

### ProjectMapper Class

Main entry point for programmatic use:

```python
from proj_mapper import ProjectMapper

# Create a mapper instance
mapper = ProjectMapper(config={
    'map_types': ['file', 'relationship'],
    'include': ['*.py', '*.md'],
    'exclude': ['**/venv/**', '**/__pycache__/**'],
    'output_dir': '.maps'
})

# Analyze a project
result = mapper.analyze_project('/path/to/project')

# Access maps
project_map = result.get_map('project')
file_maps = result.get_maps('file')

# Update maps incrementally
update_result = mapper.update_project('/path/to/project')
```

### Pipeline Stage Interface

Interface for custom pipeline stages:

```python
from proj_mapper.pipeline import PipelineStage

class CustomAnalyzer(PipelineStage):
    def process(self, context, input_data):
        # Process input data
        # ...
        return output_data
```

### Analyzer Interface

Interface for custom file analyzers:

```python
from proj_mapper.analyzers import FileAnalyzer

class CustomLanguageAnalyzer(FileAnalyzer):
    def can_analyze(self, file_path):
        # Determine if this analyzer can handle the file
        return file_path.endswith('.custom')

    def analyze(self, file_path, file_content):
        # Analyze the file
        # ...
        return analysis_result
```

## Map Output Format

### Output Directory Structure

```
.maps/
  ├── project_20231105120000.json       # Project-level map
  ├── file_myfile_20231105120000.json   # File-level map
  ├── module_mymodule_20231105120000.json  # Module-level map
  ├── relationship_20231105120000.json  # Relationship map
  ├── documentation_20231105120000.json # Documentation map
  ├── index_20231105120000.json         # Index of all maps
  └── realtime/                         # Real-time maps (updated continuously)
      ├── project_latest.json
      ├── file_myfile_latest.json
      └── relationship_latest.json
```

### Map Format (JSON)

All maps follow a common structure:

```json
{
  "schema_version": "1.0",
  "generated_at": "2023-11-05T12:00:00Z",
  "map_type": "file",
  "map_id": "unique-identifier",
  "chunk_info": {
    "chunk_index": 0,
    "total_chunks": 1,
    "next_chunk_id": null
  },
  "content": {
    // Map-specific content here
  }
}
```

### AI Agent Consumption Patterns

Maps are specifically structured for optimal consumption by AI agents:

1. **Deterministic Ordering**: All collections use deterministic ordering
2. **Explicit Typing**: Type information is included for all elements
3. **Cross-References**: Elements reference other elements using stable IDs
4. **Confidence Scores**: Inferred relationships include confidence scores
5. **Location References**: VSCode-compatible location references for navigation

Example token-optimized pattern for code elements:

```json
{
  "elements": [
    {
      "id": "func:mymodule.myfunction",
      "type": "function",
      "name": "myfunction",
      "location": {
        "file": "mymodule.py",
        "start_line": 10,
        "end_line": 20
      },
      "signature": "def myfunction(param1: str, param2: int = 0) -> bool:",
      "docstring": "Short description of function.",
      "relationships": [
        {
          "type": "calls",
          "target": "func:othermodule.otherfunction",
          "confidence": 1.0
        },
        {
          "type": "documented_by",
          "target": "doc:api.md#myfunction",
          "confidence": 0.85
        }
      ]
    }
  ]
}
```

### File Map Structure

File maps provide a detailed view of a single file:

```json
{
  "schema_version": "1.0",
  "map_type": "file",
  "file_path": "mymodule.py",
  "file_type": "python",
  "last_modified": "2023-11-05T10:30:00Z",
  "content": {
    "imports": [
      { "module": "os", "elements": ["path"] },
      { "module": "typing", "elements": ["List", "Dict"] }
    ],
    "classes": [
      {
        "name": "MyClass",
        "line_range": [10, 50],
        "methods": [
          {
            "name": "method1",
            "line_range": [15, 25],
            "signature": "def method1(self, param: str) -> bool:",
            "docstring": "Method docstring"
          }
        ],
        "attributes": [{ "name": "attr1", "line": 12, "type": "str" }]
      }
    ],
    "functions": [
      {
        "name": "my_function",
        "line_range": [55, 70],
        "signature": "def my_function(param1, param2=None):",
        "docstring": "Function docstring"
      }
    ],
    "variables": [{ "name": "CONSTANT", "line": 5, "value": "value" }]
  }
}
```

### Project Map Structure

Project maps provide a high-level view of the project:

```json
{
  "schema_version": "1.0",
  "map_type": "project",
  "project_name": "MyProject",
  "root_path": "/path/to/project",
  "content": {
    "modules": [
      {
        "name": "module1",
        "path": "module1.py",
        "summary": "Brief description of module1"
      }
    ],
    "packages": [
      {
        "name": "package1",
        "path": "package1",
        "modules": [
          {
            "name": "submodule1",
            "path": "package1/submodule1.py"
          }
        ]
      }
    ],
    "documentation": [
      {
        "name": "README",
        "path": "README.md",
        "summary": "Project readme"
      }
    ]
  }
}
```

### Relationship Map Structure

Relationship maps show connections between elements:

```json
{
  "schema_version": "1.0",
  "map_type": "relationship",
  "content": {
    "relationships": [
      {
        "source": {
          "id": "func:module1.function1",
          "type": "function",
          "location": { "file": "module1.py", "line": 10 }
        },
        "target": {
          "id": "func:module2.function2",
          "type": "function",
          "location": { "file": "module2.py", "line": 20 }
        },
        "type": "calls",
        "confidence": 1.0
      },
      {
        "source": {
          "id": "class:module1.Class1",
          "type": "class",
          "location": { "file": "module1.py", "line": 30 }
        },
        "target": {
          "id": "class:module2.Class2",
          "type": "class",
          "location": { "file": "module2.py", "line": 40 }
        },
        "type": "inherits_from",
        "confidence": 1.0
      },
      {
        "source": {
          "id": "func:module1.function1",
          "type": "function",
          "location": { "file": "module1.py", "line": 10 }
        },
        "target": {
          "id": "doc:api.md#function1",
          "type": "documentation",
          "location": { "file": "docs/api.md", "line": 50 }
        },
        "type": "documented_by",
        "confidence": 0.9
      }
    ]
  }
}
```

### Documentation Map Structure

Documentation maps show the structure of documentation:

```json
{
  "schema_version": "1.0",
  "map_type": "documentation",
  "content": {
    "documents": [
      {
        "path": "README.md",
        "title": "Project Readme",
        "sections": [
          {
            "id": "doc:README.md#introduction",
            "title": "Introduction",
            "level": 1,
            "line_range": [5, 20]
          },
          {
            "id": "doc:README.md#installation",
            "title": "Installation",
            "level": 1,
            "line_range": [22, 35]
          }
        ],
        "references": [
          {
            "type": "code",
            "target": "class:module1.Class1",
            "line": 15,
            "confidence": 0.8
          }
        ]
      }
    ]
  }
}
```

### Index Map Structure

Index maps provide a central registry of all generated maps:

```json
{
  "schema_version": "1.0",
  "map_type": "index",
  "generated_at": "2023-11-05T12:00:00Z",
  "content": {
    "maps": [
      {
        "map_id": "proj-map-123",
        "map_type": "project",
        "file_path": "project_20231105120000.json",
        "description": "Project-level map"
      },
      {
        "map_id": "file-map-124",
        "map_type": "file",
        "file_path": "file_module1_20231105120000.json",
        "description": "File map for module1.py"
      }
    ]
  }
}
```

## VSCode/Cursor IDE Integration Points

The Project Mapper provides specific integration points for VSCode-based IDEs, particularly Cursor:

### Location References

All location references in maps follow VSCode conventions:

```json
"location": {
  "file": "relative/path/to/file.py",
  "start_line": 10,
  "start_character": 4,
  "end_line": 15,
  "end_character": 7
}
```

### Real-time Map Updates

Real-time maps in the `.maps/realtime` directory provide up-to-date information that can be consumed by IDE extensions for active editing sessions.

### Map Chunking for Context Windows

Maps support chunking to fit within Cursor's AI context windows:

```json
"chunk_info": {
  "chunk_index": 0,
  "total_chunks": 3,
  "next_chunk_id": "file-map-chunk-1"
}
```

### Cursor-Specific Metadata

Maps include Cursor-specific metadata to enhance AI agent integration:

```json
"cursor_metadata": {
  "compatible_with_version": ">=0.1.0",
  "token_estimate": 1250,
  "optimized_for_models": ["claude-2", "gpt-4"]
}
```

## Configuration File Format

Configuration is stored in YAML format:

```yaml
# Project Mapper Configuration
output:
  directory: .maps
  formats:
    - json

analysis:
  include:
    - "*.py"
    - "*.md"
  exclude:
    - "**/venv/**"
    - "**/__pycache__/**"

map_types:
  - project
  - file
  - relationship
  - documentation

analyzers:
  python:
    extract_docstrings: true
    analyze_imports: true
  markdown:
    extract_references: true
    detect_code_blocks: true

relationships:
  confidence_threshold: 0.7
  infer_code_documentation_links: true

ai_optimization:
  token_efficient: true
  chunking:
    enabled: true
    max_chunk_size: 8000 # tokens
```

## Related Documents

- [Functional Requirements](../requirements/functional_requirements.md)
- [Non-Functional Requirements](../requirements/non_functional_requirements.md)
- [Data Model](../models/data_model.md)
- [System Architecture](../architecture/system_architecture.md)

---

_End of Interface Specifications Document_
