# Interface Specifications

**Version:** 1.0.0  
**Last Updated:** 2023-11-05  
**Status:** Draft

## Document Purpose

This document defines the interfaces for the Project Mapper system, including command-line interface, programming interfaces, and data exchange formats. It serves as a reference for users and developers interacting with or extending the system.

## Command Line Interface

### Synopsis

```
proj_mapper [OPTIONS] SOURCE_DIR
```

### Arguments

| Argument   | Description                                      |
| ---------- | ------------------------------------------------ |
| SOURCE_DIR | Path to the Python project to analyze (required) |

### Options

| Option                | Short | Long           | Description                          | Default    |
| --------------------- | ----- | -------------- | ------------------------------------ | ---------- |
| Output Format         | -f    | --format       | Output format (json, yaml, markdown) | json       |
| Output Directory      | -o    | --output-dir   | Directory for output files           | ./output   |
| Include Documentation | -d    | --include-docs | Enable documentation analysis        | True       |
| Documentation Path    |       | --docs-dir     | Custom documentation directory       | Autodetect |
| Code Path             |       | --code-dir     | Custom code directory                | Autodetect |
| Exclude Pattern       | -e    | --exclude      | Glob pattern for files to exclude    | None       |
| Generate File Maps    |       | --file-maps    | Generate embedded file maps          | False      |
| Clean File Maps       |       | --clean-maps   | Remove embedded file maps            | False      |
| Process Single File   |       | --file         | Process a single file                | None       |
| Recursive Processing  | -r    | --recursive    | Process directories recursively      | True       |
| Ignore File           |       | --ignore-file  | Path to .gitignore style file        | .gitignore |
| Debug Logging         |       | --debug        | Enable detailed debug logging        | False      |
| Verbose               | -v    | --verbose      | Enable verbose output                | False      |
| Quiet                 | -q    | --quiet        | Suppress all non-error output        | False      |
| Config File           | -c    | --config       | Path to configuration file           | None       |
| Show Version          |       | --version      | Display version information          | -          |
| Help                  | -h    | --help         | Show help message                    | -          |

### Examples

```bash
# Basic usage - analyze a project with default settings
proj_mapper /path/to/project

# Generate YAML output
proj_mapper -f yaml /path/to/project

# Exclude test files and save to custom directory
proj_mapper -e "*/tests/*" -o ./project_maps /path/to/project

# Focus only on code analysis, not documentation
proj_mapper --include-docs=False /path/to/project

# Use configuration file
proj_mapper -c project_mapper_config.json /path/to/project

# Analyze with custom source and documentation paths
proj_mapper --code-dir=src --docs-dir=documentation /path/to/project

# Generate embedded file maps in all project files
proj_mapper --file-maps /path/to/project

# Process a single file and generate its file map
proj_mapper --file-maps --file /path/to/project/main.py

# Remove embedded file maps from all project files
proj_mapper --clean-maps /path/to/project

# Process only specific directories recursively with file maps
proj_mapper --file-maps --recursive /path/to/project/src

# Use custom ignore patterns
proj_mapper --file-maps --ignore-file .mapignore /path/to/project

# Enable debug logging
proj_mapper --debug /path/to/project
```

## Configuration File Interface

Project Mapper accepts a JSON configuration file that can specify all command-line options, plus additional advanced settings.

### Schema

```json
{
  "source_dir": "string",
  "output": {
    "format": "string",
    "directory": "string",
    "split_by_component": "boolean",
    "max_lines_per_file": "integer"
  },
  "analysis": {
    "include_docs": "boolean",
    "docs_dir": "string",
    "code_dir": "string",
    "exclude_patterns": ["string"],
    "max_depth": "integer",
    "follow_symlinks": "boolean"
  },
  "file_maps": {
    "enabled": "boolean",
    "clean": "boolean",
    "single_file": "string",
    "recursive": "boolean",
    "ignore_file": "string"
  },
  "formatters": {
    "json": {
      "indent": "integer",
      "sort_keys": "boolean"
    },
    "yaml": {
      "default_flow_style": "boolean"
    },
    "markdown": {
      "include_toc": "boolean",
      "include_diagrams": "boolean"
    }
  },
  "logging": {
    "verbose": "boolean",
    "quiet": "boolean",
    "debug": "boolean",
    "log_file": "string"
  }
}
```

### Example Configuration

```json
{
  "source_dir": "./my_project",
  "output": {
    "format": "json",
    "directory": "./project_maps",
    "split_by_component": true,
    "max_lines_per_file": 50
  },
  "analysis": {
    "include_docs": true,
    "docs_dir": "./docs",
    "exclude_patterns": ["*/tests/*", "*/venv/*", "*/.git/*"],
    "max_depth": 10,
    "follow_symlinks": false
  },
  "file_maps": {
    "enabled": true,
    "recursive": true,
    "ignore_file": ".mapignore"
  },
  "formatters": {
    "json": {
      "indent": 2,
      "sort_keys": true
    },
    "markdown": {
      "include_toc": true,
      "include_diagrams": true
    }
  },
  "logging": {
    "verbose": true,
    "debug": false,
    "log_file": "./proj_mapper.log"
  }
}
```

## Programming Interface

Project Mapper can be used as a Python library in addition to its command-line interface.

### Core API

```python
from proj_mapper import ProjectMapper, MapperConfig

# Create configuration
config = MapperConfig(
    include_docs=True,
    output_format="json",
    exclude_patterns=["*/tests/*"]
)

# Initialize mapper
mapper = ProjectMapper(config)

# Analyze project
result = mapper.analyze_project("/path/to/project")

# Access results
project_map = result.project_map
code_structure = result.code_structure
doc_structure = result.doc_structure

# Generate output
output_files = mapper.generate_output(result)
```

### Key Classes

#### MapperConfig

Configuration object for the Project Mapper.

```python
class MapperConfig:
    def __init__(
        self,
        source_dir: Optional[str] = None,
        output_format: str = "json",
        output_dir: str = "./output",
        include_docs: bool = True,
        docs_dir: Optional[str] = None,
        code_dir: Optional[str] = None,
        exclude_patterns: List[str] = None,
        max_depth: int = 10,
        follow_symlinks: bool = False,
        max_lines_per_file: int = 50,
        split_by_component: bool = True,
        verbose: bool = False,
        quiet: bool = False,
        log_file: Optional[str] = None,
    ):
        """
        Initialize mapper configuration.

        Args:
            source_dir: Path to source directory (can be set later)
            output_format: Output format (json, yaml, markdown)
            output_dir: Directory for output files
            include_docs: Whether to include documentation analysis
            docs_dir: Custom documentation directory (None for autodetect)
            code_dir: Custom code directory (None for autodetect)
            exclude_patterns: List of glob patterns for files to exclude
            max_depth: Maximum depth for directory traversal
            follow_symlinks: Whether to follow symbolic links
            max_lines_per_file: Maximum lines per output file
            split_by_component: Whether to split output by component
            verbose: Enable verbose output
            quiet: Suppress non-error output
            log_file: Path to log file (None for no logging)
        """

    @classmethod
    def from_file(cls, config_file: str) -> "MapperConfig":
        """
        Load configuration from a file.

        Args:
            config_file: Path to JSON configuration file

        Returns:
            MapperConfig object
        """

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
```

#### ProjectMapper

Main class for analyzing projects and generating output.

```python
class ProjectMapper:
    def __init__(self, config: MapperConfig):
        """
        Initialize project mapper with configuration.

        Args:
            config: MapperConfig object
        """

    def analyze_project(self, source_dir: Optional[str] = None) -> AnalysisResult:
        """
        Analyze the specified project.

        Args:
            source_dir: Path to project directory (overrides config if provided)

        Returns:
            AnalysisResult containing the project analysis
        """

    def generate_output(
        self,
        result: AnalysisResult,
        output_format: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Generate output files from analysis result.

        Args:
            result: AnalysisResult from analyze_project
            output_format: Override output format from config
            output_dir: Override output directory from config

        Returns:
            List of generated file paths
        """
```

#### AnalysisResult

Contains the results of project analysis.

```python
class AnalysisResult:
    """Container for project analysis results."""

    project_map: ProjectModel
    code_structure: CodeStructure
    doc_structure: Optional[DocStructure]
    stats: AnalysisStats
    warnings: List[AnalysisWarning]

    def get_component(self, component_type: str, name: str) -> Optional[ModelElement]:
        """
        Get a specific component by type and name.

        Args:
            component_type: Type of component (module, class, function, etc.)
            name: Name or qualified name of the component

        Returns:
            ModelElement if found, None otherwise
        """

    def to_dict(self) -> dict:
        """
        Convert analysis result to dictionary.

        Returns:
            Dictionary representation of analysis result
        """
```

## VS Code Extension Interface

The Project Mapper VS Code extension provides integration with VS Code-based IDEs, with primary optimization for Cursor IDE.

### Extension Commands

| Command                          | Description                                  | Keybinding (Default) |
| -------------------------------- | -------------------------------------------- | -------------------- |
| `proj-mapper.generateMaps`       | Generate maps for the entire project         | Ctrl+Shift+P         |
| `proj-mapper.generateMapForFile` | Generate map for current file only           | Ctrl+Shift+M         |
| `proj-mapper.showMapOverview`    | Display map overview in side panel           | Ctrl+Shift+O         |
| `proj-mapper.findRelationships`  | Find relationships for selected entity       | Ctrl+Shift+R         |
| `proj-mapper.toggleAutoUpdate`   | Toggle automatic map updates on file changes | -                    |
| `proj-mapper.exportMaps`         | Export maps to specified location            | -                    |
| `proj-mapper.querySuggestor`     | Open map query interface with AI suggestions | Ctrl+Shift+Q         |

### Extension API

The extension exposes a JavaScript API for programmatic access from other extensions or AI agents:

```typescript
// Access Project Mapper extension API
const projMapper = vscode.extensions.getExtension(
  "proj-mapper.extension"
).exports;

// Get project map
const projectMap = await projMapper.getProjectMap();

// Get map for specific file
const fileMap = await projMapper.getFileMap("/path/to/file.py");

// Query relationships
const relationships = await projMapper.queryRelationships({
  sourceEntity: "ModuleName",
  relationshipType: "imports",
});

// Register for map update events
projMapper.onMapUpdated((event) => {
  console.log("Maps updated:", event.maps);
});

// Force map regeneration
await projMapper.regenerateMaps({
  includeDocumentation: true,
  rootPath: vscode.workspace.rootPath,
});
```

### Extension Settings

The extension adds the following settings to VS Code:

```json
{
  "proj-mapper.general.enabled": true,
  "proj-mapper.general.autoUpdateOnSave": true,
  "proj-mapper.output.path": ".cursor/maps",
  "proj-mapper.output.format": "json",
  "proj-mapper.analysis.includeDocumentation": true,
  "proj-mapper.analysis.excludePatterns": ["*/tests/*", "*/venv/*"],
  "proj-mapper.view.showMapIndicator": true,
  "proj-mapper.ai.optimizeForContextWindow": true,
  "proj-mapper.ai.enableQuerySuggestions": true
}
```

### Cursor IDE-Specific Features

When running in Cursor IDE, the extension provides additional AI-optimized features:

1. **Context Integration**: Automatically injects relevant map data into AI context
2. **Query Suggestions**: AI-powered suggestions for map queries based on current context
3. **Relationship Visualization**: Interactive visualization of code relationships with AI annotations
4. **Mapping Rules**: Support for AI-generated mapping rules to customize analysis
5. **Auto-Documentation**: Generates documentation maps from code with AI assistance

## AI Agent Consumption Interface

### Map Storage Location

Project maps are stored in a consistent location with predictable structure:

1. **Default Path**: `.cursor/maps/` in the project root directory
2. **Custom Path**: Configurable via `output.directory` setting or `--output-dir` command-line option
3. **Standard Structure**: All output locations follow the same internal organization

### Map File Naming Convention

Map files follow a consistent naming pattern:

1. **Project Overview**: `project_map.json` - Top-level project structure
2. **Module Maps**: `module_map_{module_name}.json` - Details for specific modules
3. **Relationship Maps**: `relationship_map_{type}.json` - Relationship data by type (inheritance, dependencies, etc.)
4. **Documentation Maps**: `doc_map_{doc_type}.json` - Documentation structure and content
5. **Index Map**: `map_index.json` - Central index of all generated maps with references and metadata

### Map Index Schema

The `map_index.json` file provides a central entry point for AI agents to discover available maps:

```json
{
  "version": "1.0.0",
  "generated_at": "2023-11-07T12:34:56Z",
  "project_name": "example_project",
  "maps": [
    {
      "type": "project",
      "path": "project_map.json",
      "description": "Top-level project structure and metadata",
      "entities_count": 42
    },
    {
      "type": "module",
      "path": "module_map_core.json",
      "description": "Core module structure and components",
      "entities_count": 15
    },
    {
      "type": "relationship",
      "path": "relationship_map_inheritance.json",
      "description": "Class inheritance relationships",
      "entities_count": 8
    }
  ],
  "query_examples": [
    {
      "description": "Find all modules importing 'logging'",
      "query": { "type": "dependency", "target": "logging" }
    },
    {
      "description": "List all classes with more than 5 methods",
      "query": { "type": "class", "method_count": { "$gt": 5 } }
    }
  ]
}
```

### Map Query Interface

AI agents can query maps using a simple JSON-based query language:

#### Direct Queries

```json
// Query for specific entity
{
  "entity_type": "class",
  "name": "ProjectMapper"
}

// Query for relationship
{
  "relationship_type": "inheritance",
  "source": "SpecialFormatter",
  "target": "BaseFormatter"
}

// Query with filters
{
  "entity_type": "function",
  "filters": {
    "complexity": {"$gt": 10},
    "parameters": {"$size": {"$gt": 3}}
  }
}
```

#### Query API Methods

AI agents can access the query interface programmatically through the extension API or via HTTP endpoints when enabled:

```typescript
// Extension API query
const results = await projMapper.query({
  entity_type: "module",
  filters: {
    imports: { $contains: "os" },
  },
});

// HTTP endpoint (when enabled)
fetch("http://localhost:9875/proj-mapper/query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    entity_type: "class",
    filters: { methods: { $size: { $gt: 5 } } },
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### AI Optimization Features

All map formats include specific optimizations for AI agent consumption:

1. **Token Efficiency**:

   - Short, predictable property names
   - Minimal formatting overhead
   - Abbreviated references with clear lookup paths

2. **Semantic Annotations**:

   - Purpose labels for code entities
   - Confidence scores for detected relationships
   - Pattern detection annotations

3. **Context Window Optimization**:

   - Fixed-size chunks (50 lines maximum)
   - Progressive detail loading
   - Explicit reference links between chunks

4. **AI-Friendly Data Structures**:
   - Consistent schemas across all maps
   - Explicit typing of all entities and relationships
   - Normalized data to avoid duplication

## Extension Interfaces

Project Mapper can be extended with custom analyzers, formatters, and pattern detectors.

### Custom Analyzer

```python
from proj_mapper.analyzers import Analyzer, AnalysisContext, AnalysisResult

class CustomAnalyzer(Analyzer):
    """Custom analyzer implementation."""

    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """
        Analyze the provided context and return results.

        Args:
            context: AnalysisContext containing input and configuration

        Returns:
            AnalysisResult containing the analysis outcome
        """
        # Implementation

    def get_supported_file_types(self) -> List[str]:
        """
        Get list of file extensions this analyzer supports.

        Returns:
            List of file extensions (e.g., ['.py', '.pyx'])
        """
        return ['.custom']
```

### Custom Formatter

```python
from proj_mapper.formatters import Formatter, FormatterConfig
from proj_mapper.models import ProjectModel

class CustomFormatter(Formatter):
    """Custom output formatter implementation."""

    def format(
        self,
        project_model: ProjectModel,
        config: FormatterConfig
    ) -> FormattedOutput:
        """
        Format the project model into the target output format.

        Args:
            project_model: The complete project model to format
            config: Configuration for the formatter

        Returns:
            FormattedOutput containing the formatted content
        """
        # Implementation

    def get_format_name(self) -> str:
        """
        Get the name of this formatter.

        Returns:
            Format name (e.g., 'json', 'yaml')
        """
        return 'custom'
```

### Custom Pattern Detector

```python
from proj_mapper.analyzers.patterns import PatternDetector
from proj_mapper.models import ProjectModel, Pattern

class CustomPatternDetector(PatternDetector):
    """Custom pattern detector implementation."""

    def detect_patterns(self, project_model: ProjectModel) -> List[Pattern]:
        """
        Detect patterns in the project model.

        Args:
            project_model: The complete project model

        Returns:
            List of detected patterns
        """
        # Implementation

    def get_pattern_types(self) -> List[str]:
        """
        Get list of pattern types this detector can identify.

        Returns:
            List of pattern type names
        """
        return ['custom_pattern']
```

## Data Exchange Formats

### JSON/YAML Output Format

The primary output format follows the schema defined in the Data Model document. Key sections include:

1. **Project Metadata**: Basic information about the project
2. **Structure**: Hierarchical representation of packages and modules
3. **Components**: Detailed information about classes, functions, etc.
4. **Relationships**: Dependencies, inheritance, and other relationships
5. **Patterns**: Detected architectural patterns

Example (simplified):

```json
{
  "project": {
    "name": "example_project",
    "version": "1.0.0",
    "root_path": "/path/to/project",
    "structure": {
      "packages": [...],
      "modules": [...]
    },
    "components": {
      "classes": [...],
      "functions": [...]
    },
    "relationships": {
      "dependencies": [...],
      "inheritance": [...]
    },
    "patterns": [...]
  }
}
```

For complete schema, see the [Data Model](data_model.md) document.

### Markdown Output Format

The Markdown output provides a human-readable representation of the project structure:

```markdown
# Project Map: example_project

## Overview

- **Version:** 1.0.0
- **Root Path:** /path/to/project
- **Modules:** 25
- **Packages:** 5
- **Classes:** 42
- **Functions:** 156

## Packages

### core

Core functionality for the project.

- **Modules:** 8
- **Subpackages:** utils, models

### api

API implementation and endpoints.

- **Modules:** 6
- **Subpackages:** v1, auth

...

## Modules

### core.app

Main application module.

- **Classes:** App, Configuration
- **Functions:** initialize, run
- **Imports:** logging, core.utils, typing

...

## Classes

### core.app.App

Main application class.

- **Methods:** **init**, start, stop
- **Inherits From:** None
- **Used By:** main

...
```

## Error Handling

### Exit Codes

| Code | Description             |
| ---- | ----------------------- |
| 0    | Success                 |
| 1    | General error           |
| 2    | Configuration error     |
| 3    | File access error       |
| 4    | Parsing error           |
| 5    | Output generation error |

### Warning Types

Warnings are reported but don't cause the analysis to fail:

1. **ParseWarning**: Issues parsing specific files
2. **ReferenceWarning**: Unresolved references between components
3. **PatternWarning**: Uncertain pattern detection results
4. **OutputWarning**: Issues generating specific output sections

### Error Types

Errors prevent successful completion of analysis:

1. **ConfigError**: Invalid configuration
2. **AccessError**: Unable to access required files
3. **AnalysisError**: Critical failure during analysis
4. **OutputError**: Unable to generate output files

## Related Documents

- [Data Model](data_model.md)
- [System Architecture](../architecture/system_architecture.md)
- [Functional Requirements](../requirements/functional_requirements.md)

---

_End of Interface Specifications Document_
