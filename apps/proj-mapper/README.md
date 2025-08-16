# Project Mapper

A tool for mapping and visualizing project structures and relationships.

## Overview

Project Mapper analyzes codebases to create structural maps and identify relationships between different components, helping developers understand complex projects quickly.

Key features:

- Discover and categorize files in a project
- Analyze code structure and relationships
- Extract documentation and map it to code
- Generate visualizations of project structure
- Support for incremental updates

## Installation

```bash
# From PyPI (once published)
pip install proj-mapper

# From source
git clone https://github.com/yourusername/proj_mapper.git
cd proj_mapper
pip install -e .
```

## Usage

### Command Line

```bash
# Analyze a project (writes a map to <project>/.maps/project_map.json)
PYTHONPATH=apps/proj-mapper/src python apps/proj-mapper/src/proj_mapper/cli/main.py analyze /path/to/project

# Update an existing analysis (incremental flag reserved; currently performs full re-analysis)
PYTHONPATH=apps/proj-mapper/src python apps/proj-mapper/src/proj_mapper/cli/main.py update /path/to/project

# Generate visualizations (DOT is reliable without extra deps)
PYTHONPATH=apps/proj-mapper/src python apps/proj-mapper/src/proj_mapper/cli/main.py visualize /path/to/project -f dot -o /path/to/project/.maps/visualization.dot

# Generate HTML visualization
# If Graphviz (binary 'dot') and python 'graphviz' are installed, SVG will be embedded in HTML.
# Otherwise, a basic dependency-free HTML will be created.
PYTHONPATH=apps/proj-mapper/src python apps/proj-mapper/src/proj_mapper/cli/main.py visualize /path/to/project -f html -o /path/to/project/.maps/visualization.html
```

Notes:
- The visualize command verifies the output file exists before reporting success.
- HTML rendering prefers Graphviz for rich SVG; if unavailable, a basic HTML fallback is produced so you always get a file.
- For installed package usage, replace the long PYTHONPATH calls with your console entry point when available.

### Smoke test

A quick end-to-end smoke test script is available:

```bash
apps/proj-mapper/scripts/smoke_test.sh
```

It will:
- Run analyze on the `apps/proj-mapper/src` tree
- Generate DOT and HTML visualizations
- Verify the output files exist and print their sizes

### Python API

```python
from proj_mapper.core.project_manager import ProjectManager

manager = ProjectManager()
project_map = manager.analyze_project("/path/to/project")
print(len(project_map.files))
```

## Configuration

Project Mapper can be configured through:

- Command line arguments
- Configuration files (YAML or JSON)
- Environment variables
- Python API

Example configuration file (`proj_mapper.yaml`):

```yaml
project_name: My Project
output_dir: .maps
include_patterns:
  - "**/*.py"
  - "**/*.md"
exclude_patterns:
  - "**/venv/**"
  - "**/node_modules/**"
max_file_size: 1048576 # 1MB
analyze_code: true
analyze_docs: true
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
flake8
mypy src
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
