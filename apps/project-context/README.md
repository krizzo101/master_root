# Project Context MCP Server

## Overview
MCP server providing semantic access to project intelligence data from `.proj-intel/` directories.

## Features
- 21 semantic tools for accessing project intelligence
- Complete abstraction of `.proj-intel/` implementation details
- Multi-level caching for performance
- Async/await patterns throughout
- Built with FastMCP framework

## Installation
```bash
cd apps/project-context
pip install -e .
```

## Usage
```bash
project-context serve
```

## Tools
- `get_project_summary` - Overall project statistics
- `find_files` - Search for files by pattern
- `get_file_info` - Detailed file information
- `find_symbols` - Search for functions/classes
- `get_dependencies` - Project dependency graph
- `find_agents` - Discover agent architectures
- `get_entry_points` - Find CLI/main entries
- `get_api_endpoints` - List API routes
- `get_data_models` - Find data structures
- `get_tests` - Test file mapping
- `get_config` - Configuration overview
- `get_quality_metrics` - Code quality stats
- `get_recent_changes` - Recent modifications
- `search_code` - Full-text code search
- `get_call_graph` - Function relationships
- `get_imports` - Import analysis
- `get_complexity` - Complexity metrics
- `get_documentation` - Doc coverage
- `get_todos` - TODO/FIXME items
- `get_security_issues` - Security concerns
- `validate_intelligence` - Data integrity check

## Development
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```
