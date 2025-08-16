# Auto-Attach Script Documentation

## Overview

The auto-attach script provides intelligent file dependency analysis for the consult agent gatekeeper functionality. It automatically finds related files based on import relationships, directory structure, and file types.

## Components

### 1. Auto-Attach Generator (`auto_attach_generator.py`)

Generates optimized `file_dependencies.json` from existing `project_map.yaml` data.

**Usage:**
```bash
python scripts/auto_attach_generator.py --project-map .proj-intel/project_map.yaml --output .proj-intel/file_dependencies.json
```

**Features:**
- Extracts import relationships from project map
- Classifies files by type (source, config, test, documentation)
- Builds optimized indexes for fast lookups
- Creates bidirectional import relationships
- Normalizes import statements

### 2. Auto-Attach Script (`auto_attach.py`)

Main script that uses the generated dependencies to find related files.

**Usage:**
```bash
# Basic usage
python scripts/auto_attach.py file1.py file2.py

# With custom dependencies file
python scripts/auto_attach.py file1.py --dependencies .proj-intel/file_dependencies.json

# With detailed analysis
python scripts/auto_attach.py file1.py --analyze

# Save results to file
python scripts/auto_attach.py file1.py --output results.json
```

**Features:**
- O(1) file lookups using pre-computed indexes
- Finds imported files and files that import the target
- Discovers files in the same directory
- Identifies related configuration and test files
- Provides detailed analysis and filtering

### 3. Test Suite (`test_auto_attach.py`)

Comprehensive test suite for the auto-attach functionality.

**Usage:**
```bash
python scripts/test_auto_attach.py
```

## File Format

The auto-attach system uses an optimized JSON format (`file_dependencies.json`) with the following structure:

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
      "path/to/dir": ["file1.py", "file2.py"]
    },
    "by_import": {
      "module1": ["file1.py", "file2.py"]
    },
    "by_type": {
      "source": ["file1.py", "file2.py"],
      "config": ["config1.json"],
      "test": ["test1.py"],
      "documentation": ["readme.md"]
    }
  },
  "metadata": {
    "generated_at": "2025-08-07T13:05:58.123456",
    "total_files": 521,
    "base_path": "/home/opsvi/master_root",
    "schema_version": "1.0.0"
  }
}
```

## File Type Classification

### Source Files
- **Criteria**: Python files with `.py` extension that contain code
- **Examples**: `mcp_agent_server.py`, `challenge_agent.py`

### Configuration Files
- **Criteria**: Files that configure the project or its dependencies
- **Examples**: `package.json`, `requirements.txt`, `pyproject.toml`, `setup.py`, `.env`, `config.py`, `settings.py`

### Test Files
- **Criteria**: Files that test other files
- **Patterns**: `test_*.py`, `*_test.py`, `*Test.py`, `*_spec.py`, `*Spec.py`

### Documentation Files
- **Criteria**: Files that document the project
- **Examples**: `README.md`, `docs/*.md`, `*.rst`, `*.txt`

## Auto-Attach Algorithm

The auto-attach script finds related files using the following logic:

1. **Imported Files**: Files that the target file imports
2. **Importing Files**: Files that import the target file
3. **Same Directory**: All files in the same directory as the target
4. **Configuration Files**: Config files in the same directory
5. **Test Files**: Related test files (based on naming patterns)

## Performance Characteristics

- **File Lookup**: O(1) using dictionary keys
- **Directory Queries**: O(1) using pre-computed indexes
- **Import Queries**: O(1) using pre-computed indexes
- **Type Filtering**: O(1) using pre-computed indexes
- **Memory Usage**: Optimized for minimal data storage

## Integration with Consult Agent

The auto-attach script is designed to work with the consult agent gatekeeper:

1. **Pre-Attachment**: Auto-attach script finds related files before nano analysis
2. **Nano Filtering**: The `gpt-4.1-nano` agent filters the pre-attached files
3. **Context Optimization**: Only relevant files are sent to the main model

## Example Workflow

```python
# 1. Generate dependencies (run once)
python scripts/auto_attach_generator.py

# 2. Use auto-attach in consult agent
from scripts.auto_attach import AutoAttach

auto_attach = AutoAttach(".proj-intel/file_dependencies.json")
auto_attach.load_dependencies()

# User provides a file
user_file = "libs/opsvi-security/opsvi_security/core.py"

# Auto-attach finds related files
related_files = auto_attach.find_related_files([user_file])
# Result: 10 related files including imports, configs, tests, etc.

# Nano agent can now filter these files
filtered_files = nano_filter_files(related_files, user_request)
```

## Demo Files

- **Full Dependencies**: `.proj-intel/file_dependencies.json` (521 files)
- **Demo Dependencies**: `.proj-intel/file_dependencies_demo.json` (16 files)

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_auto_attach.py
```

The test suite covers:
- Basic functionality
- Multiple file handling
- File analysis
- Filtering by type
- Index lookups

## Benefits

1. **Performance**: O(1) lookups for all operations
2. **Accuracy**: Based on actual import relationships
3. **Completeness**: Finds all related file types
4. **Flexibility**: Supports filtering and analysis
5. **Integration**: Designed for consult agent workflow

## Future Enhancements

- Support for more file types and patterns
- Enhanced import relationship analysis
- Integration with Neo4j for complex queries
- Real-time dependency updates
- Advanced filtering algorithms
