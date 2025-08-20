# Library Action Plan - Prioritized by Usage

## Current Usage Analysis

Based on scanning all apps, only 2 opsvi libraries are actively used:
- **opsvi-mcp**: Used by proj-mapper (claude_code_adapter.py)
- **opsvi-interfaces**: Used by proj-mapper (created for CLI/config)

This means we have significant freedom to consolidate without breaking existing apps.

## Immediate Actions (Do Now)

### 1. Remove Empty Stub Libraries
These have 0 files and serve no purpose:
```bash
rm -rf libs/opsvi-communication
rm -rf libs/opsvi-coordination
rm -rf libs/opsvi-orchestration
rm -rf libs/opsvi-sdlc-enhancements
```

### 2. Keep Only Essential Libraries

#### Tier 1: Currently Used (Keep & Complete)
- **opsvi-mcp** ✅ (Already complete, has setup.py)
- **opsvi-interfaces** ⚠️ (Needs completion, has setup.py)

#### Tier 2: Core Infrastructure (Keep & Add setup.py)
- **opsvi-core** - Base classes and patterns
- **opsvi-data** - Data models and schemas
- **opsvi-llm** - LLM interfaces (Anthropic, OpenAI)

#### Tier 3: Useful Utilities (Keep if Needed)
- **opsvi-visualization** - For proj-mapper outputs
- **opsvi-fs** - File system utilities
- **opsvi-auth** - If we need auth

### 3. Libraries to Archive/Remove

Since they're not used by any apps:
- **opsvi-agents** (139 files) → Archive, replaced by opsvi-mcp
- **opsvi-auto-forge** (139 files) → Archive, migrate if needed
- **opsvi-memory** (13 files) → Remove, use Neo4j
- **opsvi-workers** (3 files) → Remove
- **opsvi-orchestrator** (2 files) → Remove
- **opsvi-comm** (11 files) → Archive
- **opsvi-coord** (6 files) → Archive

### 4. Large Libraries to Review

These need investigation before deciding:
- **opsvi-ecosystem** (1126 files) - Likely contains duplicates
- **opsvi-docs** (1590 files) - May just be documentation
- **opsvi-asea** (381 files) - Unknown purpose
- **opsvi-shared** (301 files) - May have useful utilities

## Execution Script

```bash
#!/bin/bash
# Clean up unused libraries

# 1. Create archive directory
mkdir -p libs/ARCHIVED

# 2. Remove empty stubs (no value to archive)
echo "Removing empty stub libraries..."
rm -rf libs/opsvi-communication
rm -rf libs/opsvi-coordination
rm -rf libs/opsvi-orchestration
rm -rf libs/opsvi-sdlc-enhancements

# 3. Archive unused but substantial libraries
echo "Archiving unused libraries..."
for lib in opsvi-agents opsvi-auto-forge opsvi-memory opsvi-workers opsvi-orchestrator opsvi-comm opsvi-coord; do
    if [ -d "libs/$lib" ]; then
        echo "  Archiving $lib..."
        mv "libs/$lib" "libs/ARCHIVED/"
    fi
done

# 4. Add setup.py to core libraries
echo "Adding setup.py to core libraries..."
for lib in opsvi-core opsvi-data opsvi-llm opsvi-fs opsvi-auth opsvi-visualization; do
    if [ -d "libs/$lib" ] && [ ! -f "libs/$lib/setup.py" ]; then
        echo "  Creating setup.py for $lib..."
        python scripts/create_setup_py.py "libs/$lib"
    fi
done

echo "Cleanup complete!"
```

## Final Library Structure

After consolidation, we'll have ~10 focused libraries:

### Core (3)
1. **opsvi-core** - Base abstractions
2. **opsvi-data** - Data models
3. **opsvi-llm** - LLM interfaces

### Infrastructure (3)
4. **opsvi-mcp** - Claude-code MCP server
5. **opsvi-interfaces** - CLI/config interfaces
6. **opsvi-fs** - File operations

### Optional Utilities (4)
7. **opsvi-visualization** - Diagrams/outputs
8. **opsvi-auth** - Authentication (if needed)
9. **opsvi-monitoring** - Metrics/logging (if needed)
10. **opsvi-docker** - Container management (if needed)

## Benefits of This Approach

1. **Minimal Disruption**: Only 2 libs are actually used
2. **Clean Architecture**: 10 focused libraries vs 36 mixed
3. **Easy Maintenance**: Each library has clear purpose
4. **Standardization**: Everything uses opsvi-mcp for agents
5. **No Breaking Changes**: Existing apps continue working

## Next Steps After Cleanup

1. Complete opsvi-interfaces implementation
2. Add comprehensive tests to opsvi-core
3. Document public APIs in opsvi-llm
4. Migrate auto-forge-factory to use opsvi-mcp
5. Create example apps showing proper library usage
