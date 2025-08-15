# Configuration Guide

Project Mapper can be configured to analyze different types of files, detect various relationships, and customize output formats. This guide explains all available configuration options.

## Configuration File Format

Project Mapper uses JSON for configuration files. The configuration consists of these main sections:

- `project`: Basic project information
- `analyzers`: Configuration for different file analyzers
- `output`: Output format and location settings
- `relationships`: Relationship detection and filtering settings

## Creating a Configuration File

You can create a configuration file manually or generate a default one:

```bash
# Generate a default configuration file
proj-mapper init-config --output my_config.json
```

## Configuration Sections

### Project Configuration

The `project` section contains basic information about your project:

```json
"project": {
    "name": "my_project",
    "root": "/path/to/your/project",
    "description": "Optional project description"
}
```

| Field         | Type   | Required | Description                                                        |
| ------------- | ------ | -------- | ------------------------------------------------------------------ |
| `name`        | string | Yes      | The name of your project                                           |
| `root`        | string | No       | The root directory of your project (defaults to current directory) |
| `description` | string | No       | A description of your project                                      |

### Analyzer Configuration

The `analyzers` section configures which analyzers to use and how they should operate:

```json
"analyzers": {
    "python": {
        "enabled": true,
        "include_patterns": ["**/*.py"],
        "exclude_patterns": ["**/test_*.py", "**/conftest.py"],
        "parser_options": {
            "parse_docstrings": true,
            "detect_imports": true
        }
    },
    "markdown": {
        "enabled": true,
        "include_patterns": ["**/*.md"],
        "exclude_patterns": [],
        "parser_options": {
            "extract_code_blocks": true,
            "detect_references": true
        }
    }
}
```

Each analyzer has these common fields:

| Field              | Type    | Required | Description                        |
| ------------------ | ------- | -------- | ---------------------------------- |
| `enabled`          | boolean | Yes      | Whether the analyzer is active     |
| `include_patterns` | array   | No       | Glob patterns for files to include |
| `exclude_patterns` | array   | No       | Glob patterns for files to exclude |
| `parser_options`   | object  | No       | Analyzer-specific options          |

#### Python Analyzer Options

| Option             | Type    | Default | Description                                            |
| ------------------ | ------- | ------- | ------------------------------------------------------ |
| `parse_docstrings` | boolean | true    | Extract information from docstrings                    |
| `detect_imports`   | boolean | true    | Detect import relationships                            |
| `parse_type_hints` | boolean | true    | Extract type hint information                          |
| `include_private`  | boolean | false   | Include private methods/attributes (prefixed with `_`) |

#### Markdown Analyzer Options

| Option                | Type    | Default | Description                        |
| --------------------- | ------- | ------- | ---------------------------------- |
| `extract_code_blocks` | boolean | true    | Parse and analyze code blocks      |
| `detect_references`   | boolean | true    | Detect references to code elements |
| `extract_headers`     | boolean | true    | Extract header structure           |
| `include_frontmatter` | boolean | true    | Parse YAML frontmatter             |

### Output Configuration

The `output` section controls how the map is generated and stored:

```json
"output": {
    "format": "json",
    "directory": ".maps",
    "filename_template": "{project_name}.{format}",
    "prettify": true,
    "chunking": {
        "enabled": true,
        "chunk_size": 1000,
        "max_chunks": 10
    }
}
```

| Field               | Type    | Required | Description                                    |
| ------------------- | ------- | -------- | ---------------------------------------------- |
| `format`            | string  | Yes      | Output format (`json` only in current version) |
| `directory`         | string  | No       | Directory to store maps (defaults to `.maps`)  |
| `filename_template` | string  | No       | Template for output filenames                  |
| `prettify`          | boolean | No       | Whether to format output for readability       |
| `chunking`          | object  | No       | Configuration for chunking large maps          |

#### Chunking Options

| Field        | Type    | Required | Description                                |
| ------------ | ------- | -------- | ------------------------------------------ |
| `enabled`    | boolean | No       | Whether to enable chunking (default: true) |
| `chunk_size` | number  | No       | Maximum size for each chunk (in tokens)    |
| `max_chunks` | number  | No       | Maximum number of chunks to create         |

### Relationship Configuration

The `relationships` section controls how relationships are detected and filtered:

```json
"relationships": {
    "confidence_threshold": 0.5,
    "include_types": ["imports", "defines", "references", "documented_by"],
    "exclude_types": [],
    "bidirectional": true,
    "max_distance": 3
}
```

| Field                  | Type    | Required | Description                                         |
| ---------------------- | ------- | -------- | --------------------------------------------------- |
| `confidence_threshold` | number  | No       | Minimum confidence score (0-1) for relationships    |
| `include_types`        | array   | No       | Relationship types to include (empty = all)         |
| `exclude_types`        | array   | No       | Relationship types to exclude                       |
| `bidirectional`        | boolean | No       | Whether to include relationships in both directions |
| `max_distance`         | number  | No       | Maximum distance for indirect relationships         |

## Configuration Priority

Configuration is loaded in this order (later sources override earlier ones):

1. Default configuration built into Project Mapper
2. Configuration file in the project root (`.proj_mapper.json` or `proj_mapper.json`)
3. Configuration file specified with `--config` option
4. Command-line arguments

## Environment Variables

Some configuration can be provided through environment variables:

- `PROJ_MAPPER_CONFIG`: Path to a configuration file
- `PROJ_MAPPER_OUTPUT_DIR`: Output directory for maps
- `PROJ_MAPPER_FORMAT`: Output format
- `PROJ_MAPPER_PROJECT_ROOT`: Project root directory

## Example Configuration

Here's a complete example configuration:

```json
{
  "project": {
    "name": "my_project",
    "root": "/path/to/your/project",
    "description": "My awesome Python project"
  },
  "analyzers": {
    "python": {
      "enabled": true,
      "include_patterns": ["**/*.py"],
      "exclude_patterns": ["**/test_*.py", "**/conftest.py"],
      "parser_options": {
        "parse_docstrings": true,
        "detect_imports": true,
        "parse_type_hints": true,
        "include_private": false
      }
    },
    "markdown": {
      "enabled": true,
      "include_patterns": ["**/*.md"],
      "exclude_patterns": [],
      "parser_options": {
        "extract_code_blocks": true,
        "detect_references": true,
        "extract_headers": true,
        "include_frontmatter": true
      }
    }
  },
  "output": {
    "format": "json",
    "directory": ".maps",
    "filename_template": "{project_name}.{format}",
    "prettify": true,
    "chunking": {
      "enabled": true,
      "chunk_size": 1000,
      "max_chunks": 10
    }
  },
  "relationships": {
    "confidence_threshold": 0.5,
    "include_types": ["imports", "defines", "references", "documented_by"],
    "exclude_types": [],
    "bidirectional": true,
    "max_distance": 3
  }
}
```
