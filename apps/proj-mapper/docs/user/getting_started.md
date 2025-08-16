# Getting Started with Project Mapper

This guide will help you get started with Project Mapper, a tool for analyzing Python projects and generating structured maps optimized for AI agent consumption.

## Installation

You can install Project Mapper using pip:

```bash
pip install proj-mapper
```

For development installation, clone the repository and install in development mode:

```bash
git clone https://github.com/yourusername/project_mapper.git
cd project_mapper
pip install -e .
```

## Quick Start

### Basic Usage

The simplest way to use Project Mapper is to run it on a Python project directory:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Generate a project map
proj-mapper generate-map
```

This will:

1. Analyze all Python and Markdown files in the current directory
2. Detect relationships between code and documentation
3. Generate a map file in the `.maps` directory

### Command Line Interface

Project Mapper provides several commands:

1. **Generate a Map**:

   ```bash
   proj-mapper generate-map [--config CONFIG_FILE] [--output-dir OUTPUT_DIR]
   ```

2. **Analyze Only**:

   ```bash
   proj-mapper analyze [--config CONFIG_FILE]
   ```

3. **Validate Configuration**:

   ```bash
   proj-mapper validate-config [--config CONFIG_FILE]
   ```

4. **Help**:
   ```bash
   proj-mapper --help
   ```

### Using Configuration Files

Project Mapper can be configured using a JSON configuration file:

```bash
proj-mapper generate-map --config my_config.json
```

Example configuration file (`my_config.json`):

```json
{
  "project": {
    "name": "my_project",
    "root": "/path/to/your/project"
  },
  "analyzers": {
    "python": {
      "enabled": true,
      "include_patterns": ["**/*.py"],
      "exclude_patterns": ["**/test_*.py", "**/conftest.py"]
    },
    "markdown": {
      "enabled": true,
      "include_patterns": ["**/*.md"],
      "exclude_patterns": []
    }
  },
  "output": {
    "format": "json",
    "directory": ".maps",
    "chunking": {
      "enabled": true,
      "chunk_size": 1000
    }
  },
  "relationships": {
    "confidence_threshold": 0.5,
    "include_types": ["imports", "defines", "references", "documented_by"]
  }
}
```

## Next Steps

- Explore the [Configuration Guide](configuration.md) for detailed configuration options
- Check the [CLI Reference](cli_reference.md) for all available commands and options
- Learn about [Advanced Usage](advanced_usage.md) scenarios
- See the [Troubleshooting](troubleshooting.md) guide if you encounter any issues
