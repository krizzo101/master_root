# MCP Registry Builder Specification

## Overview
This specification details the implementation for merging and managing MCP registry configurations to create a master registry for dynamic agent architectures.

## File Locations

### Input Files
1. **Primary MCP Config**: `/home/opsvi/master_root/.mcp.json`
2. **Backup MCP Config**: `/home/opsvi/master_root/.mcp.json.backup.2025-09-07-00-24-14`

### Output File
- **Master Registry**: `/home/opsvi/master_root/apps/agent-orchestrator/master_mcp_registry.json`

## Implementation Details

### 1. Registry Builder Function Location
**File**: `src/unified/mcp_registry_builder.py` (NEW FILE)

### 2. Merge Strategy

#### Algorithm
```python
def merge_mcp_configs(primary_path: Path, backup_path: Path) -> Dict:
    """
    Merge MCP configurations with intelligent deduplication.

    Strategy:
    1. Load both configurations
    2. Use primary as base
    3. Add unique servers from backup
    4. For duplicates, prefer primary but log differences
    5. Validate merged configuration
    """
```

#### Deduplication Rules
1. **Server Name Conflicts**: If same server name exists in both:
   - Keep primary version
   - Log differences in a separate file
   - Add backup version with suffix (e.g., `knowledge` → `knowledge_backup`)

2. **Environment Variable Handling**:
   - Merge environment variables for same server
   - Primary values take precedence
   - Log any API key differences for security audit

### 3. Validation Steps

#### Structure Validation
```python
def validate_mcp_registry(registry: Dict) -> Tuple[bool, List[str]]:
    """
    Validate master registry structure.

    Checks:
    1. Required fields: mcpServers
    2. Each server has: command, args
    3. Optional fields properly formatted: env, cwd
    4. No circular dependencies
    5. Valid file paths for local commands
    """
```

#### Security Validation
- Check for exposed credentials
- Validate API key formats
- Ensure no duplicate sensitive keys
- Log all API keys found (masked)

### 4. Integration Points

#### Orchestrator Integration
**File**: `src/generic_orchestrator.py`
**Line**: 223 (in `__init__` method, optimization section)

```python
# Add after line 222
if hasattr(self, 'master_mcp_registry_path') and self.master_mcp_registry_path:
    mcp_config = self.load_master_registry(self.master_mcp_registry_path)
else:
    # Existing minimal research config
```

#### UnifiedOrchestrator Integration
**File**: `src/unified/unified_orchestrator.py`
**Line**: 168 (in `__init__` method)

```python
# Add parameter to UnifiedConfig dataclass (line 65)
master_mcp_registry_path: Optional[Path] = None
```

### 5. Command-Line Tool

Create standalone script for registry building:

**File**: `scripts/build_mcp_registry.py`

```python
#!/usr/bin/env python3
"""
Build master MCP registry from multiple sources.

Usage:
    python scripts/build_mcp_registry.py \
        --primary /home/opsvi/master_root/.mcp.json \
        --backup /home/opsvi/master_root/.mcp.json.backup.2025-09-07-00-24-14 \
        --output master_mcp_registry.json
"""
```

### 6. Registry Structure

#### Expected Output Format
```json
{
  "mcpServers": {
    // All unique servers from both configs
  },
  "metadata": {
    "created": "ISO timestamp",
    "sources": ["primary_path", "backup_path"],
    "total_servers": 20,
    "duplicates_found": 5,
    "merge_strategy": "primary_precedence"
  }
}
```

### 7. Error Handling

#### Failure Modes
1. **Missing Files**: Log warning, continue with available
2. **Invalid JSON**: Fail with clear error message
3. **Merge Conflicts**: Log conflicts, use primary
4. **Validation Failures**: Return detailed error list

#### Recovery Strategy
- Always keep backup of original configs
- Create timestamped versions of master registry
- Provide rollback mechanism

### 8. Testing Requirements

#### Unit Tests
- Test merge with no conflicts
- Test merge with duplicate servers
- Test merge with different env vars
- Test validation of merged config
- Test error handling for missing files

#### Integration Tests
- Test loading in GenericOrchestrator
- Test loading in UnifiedOrchestrator
- Test dynamic MCP config generation

### 9. Implementation Order

1. Create `mcp_registry_builder.py` module
2. Implement merge logic
3. Add validation functions
4. Create command-line tool
5. Integrate with orchestrators
6. Add tests

### 10. Code Patterns to Look For

#### In Existing Code
- Line 223-261 in `generic_orchestrator.py`: MCP config generation
- Line 65-113 in `unified_orchestrator.py`: UnifiedConfig dataclass
- Environment variable handling patterns

#### Key Functions to Modify
1. `GenericOrchestrator.__init__` (line 171-276)
2. `UnifiedConfig` dataclass (line 65-113)
3. MCP config generation section (line 223-261)

### 11. Backward Compatibility

- Default to existing behavior if no master registry specified
- Support both old and new initialization patterns
- Maintain existing MCP config structure

### 12. Debug Output

When building registry:
```
[INFO] Loading primary config: /home/opsvi/master_root/.mcp.json
[INFO] Found 7 servers in primary
[INFO] Loading backup config: .mcp.json.backup.2025-09-07-00-24-14
[INFO] Found 15 servers in backup
[INFO] Merging configurations...
[INFO] Duplicate found: knowledge (keeping primary)
[INFO] Duplicate found: thinking (keeping primary)
[INFO] Total unique servers: 20
[INFO] Writing master registry: master_mcp_registry.json
[INFO] Registry build complete
```

## Safety Considerations

1. **NO TokenPool Modifications**: Registry builder must not touch token handling
2. **Optional Parameters Only**: All new parameters must have defaults
3. **Preserve Existing Behavior**: Must work without master registry
4. **Validation Before Use**: Always validate before loading in orchestrator
