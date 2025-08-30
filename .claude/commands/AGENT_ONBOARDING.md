---
description: Consume and analyze project intelligence artifacts from .proj-intel/ directories
tags: [analysis, project-intelligence, context]
---

# Project Intelligence Artifacts Consumer

Consume and analyze the generated project intelligence context package from `.proj-intel/` directories.

**IMPORTANT**: These instructions apply to ANY `.proj-intel/` directory regardless of its location in the filesystem. The `.proj-intel/` directory contains a mapping of its parent directory and all subdirectories/files within scope.

## Core Artifacts to Process

First, identify the location of the `.proj-intel/` directory you need to analyze:
!ls -la .proj-intel/ 2>/dev/null || find . -type d -name ".proj-intel" | head -5

Process these primary artifacts:

1. **Primary JSONL**: `.proj-intel/project_analysis.jsonl`
   - Newline-delimited JSON with three record kinds: metadata, collector, collector_item
   - Each line has minimal stable keys; items include a checksum and valid flag

2. **Index**: `.proj-intel/project_analysis.index.json`
   - Records: line, byte_offset, byte_size, kind, collector, optional identifiers (file_path, name)
   - Summary: counts per collector and collector_item

3. **Project Map**: `.proj-intel/project_map.yaml`
   - One-line-per-file list honoring .gitignore
   - Use for scoping and navigation

## Agent-Optimized Helpers

Utilize these optimized indices for efficient data access:

- **Reverse Index**: `.proj-intel/reverse_index.json` - O(1) path to JSONL byte ranges
- **Symbol Index**: `.proj-intel/symbol_index.json` - O(1) symbol/class to file/offset
- **Blocks Index**: `.proj-intel/blocks.index.json` - Merged adjacent byte ranges
- **Manifest**: `proj_intel_manifest.json` - Lists primary, shards, indices

### Available Shards
- `.proj-intel/file_elements.min.jsonl` - Minimal file metadata
- `.proj-intel/file_elements.jsonl` - Full file element items
- `.proj-intel/agent_architecture.jsonl` - Agent/class definitions

## CRITICAL: Data Reading Protocol

**DO NOT attempt to implement byte-offset reading yourself!**

Use the **Project Intelligence Byte-Offset Reader** - a specialized tool that implements the proper byte-offset reading strategy for efficient data access from `.proj-intel/` directories. Standard file reading tools cannot seek to byte positions correctly.

Execute the reader script for proper data access:
!python scripts/proj_intel_reader.py --help

**Script Location**: `scripts/proj_intel_reader.py` (relative to project root)
**Purpose**: Implements memory-efficient streaming and byte-offset reading for large JSONL files

### Essential Reading Commands

The script supports 6 primary actions for data extraction:

```bash
# Get file statistics - shows functions and classes per file
!python scripts/proj_intel_reader.py --action file-elements --limit 10 --format summary

# Read all project intelligence items for a specific file path
!python scripts/proj_intel_reader.py --action read-by-path --path "src/main.py"

# Stream items from a specific collector (memory-efficient)
!python scripts/proj_intel_reader.py --action read-collector --collector FileElementsCollector

# Find and list agent/class definitions in the project
!python scripts/proj_intel_reader.py --action agents --format summary

# Read specific byte ranges directly from JSONL (for targeted access)
!python scripts/proj_intel_reader.py --action read-bytes --offset 1024 --size 512

# Stream entire JSONL line by line (memory-efficient for large files)
!python scripts/proj_intel_reader.py --action stream-jsonl --limit 100
```

**Output Formats**:
- `--format json`: Full JSON output with all details
- `--format summary`: Human-readable summary format

## Recommended Ingestion Sequence

Follow this order for optimal data consumption:

1. Verify manifest and schema:
   !cat proj_intel_manifest.json | python -m json.tool | head -20

2. Get file overview:
   !python scripts/proj_intel_reader.py --action file-elements --format summary

3. Analyze specific files:
   !python scripts/proj_intel_reader.py --action read-by-path --path "$TARGET_PATH"

4. Discover agents:
   !python scripts/proj_intel_reader.py --action agents --format summary

5. Stream collector data:
   !python scripts/proj_intel_reader.py --action read-collector --collector $COLLECTOR_NAME

## Collector Reference

Understand each collector's purpose:

| Collector | Purpose |
|-----------|---------|
| **FileElementsCollector** | Functions, classes, imports with content_hash |
| **AgentArchitectureCollector** | Discovered agents with methods and docstrings |
| **EntryPointsCollector** | CLI and module entry points |
| **DependenciesCollector** | Import edges, cycles, most imported |
| **ApiEndpointsCollector** | HTTP endpoints (FastAPI/Flask) |
| **DataModelsCollector** | Pydantic/SQLAlchemy/dataclass models |
| **ConfigEnvCollector** | Config files and environment variables |
| **TestsTopologyCollector** | Test files and target mapping |
| **DepsExtendedCollector** | Third-party imports and version constraints |
| **QualityQuickCollector** | Metrics, complexity, lint summary |
| **CallGraphCollector** | Function calls per file |
| **ChangesetCollector** | Added/removed/modified since previous build |

## Performance Guidelines

Implement these practices for optimal performance:

- **Stream data** - Never load project_analysis.jsonl entirely into memory
- **Use indices** - Prefer byte_offset/byte_size from index for direct seeks
- **Batch I/O** - Group nearby offsets; respect blocks.index.json
- **Validate data** - Skip items with valid=false or checksum mismatch

## Access Pattern Examples

Use these patterns for common operations:

```bash
# Fetch all FileElements items
# Filter index.records for collector=="FileElementsCollector" then read those lines

# Fetch by path
# Read reverse_index.json[path] -> seek project_analysis.jsonl at byte_offset/size

# Fetch agent classes
# Stream agent_architecture.jsonl or pull AgentArchitectureCollector items
```

## Safety Considerations

Remember these assumptions and constraints:

- .gitignore and dot-directories were honored during collection
- Collectors may set data.partial=true if time budgets were reached
- JSONL items include checksums for integrity verification
- Debug logs are in pi.debug.log - do not print to console context

## Quick Validation

Verify the integrity of the project intelligence data:

```bash
# Check if all expected files exist
!ls -la .proj-intel/*.json .proj-intel/*.jsonl .proj-intel/*.yaml 2>/dev/null | wc -l

# Verify manifest structure
!python -c "import json; m=json.load(open('proj_intel_manifest.json')); print(f'Schema: {m.get(\"schema_version\")}, Shards: {len(m.get(\"shards\", []))}')"

# Quick collector summary
!python scripts/proj_intel_reader.py --action file-elements --limit 1 --format summary
```
