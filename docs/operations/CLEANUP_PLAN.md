# Master Root Cleanup Plan
Generated: 2025-08-24

## 1. Knowledge System Cleanup

### KEEP (6 core files):
- `embedding_service.py` - Embedding generation service
- `simple_rag.py` - Vector search used by ACCF
- `mcp_knowledge_server.py` - MCP server implementation
- `mcp_knowledge_tools.py` - MCP tool definitions
- `claude_knowledge_retrieval.py` - Claude-specific retrieval
- `fast_ingest.py` - Fast ingestion pipeline

### EVALUATE Before Deletion (5 advanced features):
- `autonomous_evolution.py` - Self-improvement engine (UNIQUE - probably keep)
- `adaptive_learning.py` - Learns from usage patterns
- `unified_intelligent_search.py` - Advanced multi-source search
- `knowledge_synthesis.py` - Pattern synthesis across knowledge
- `predictive_prefetch.py` - Pre-loads likely needed knowledge

### DELETE (50+ files):
- `memory_crystal.py` - Obsolete experiment
- All `*test*.py` files not in tests/ directory
- All `*demo*.py` files
- `letta_integration.py` - Not using Letta
- Duplicate implementations
- Old experimental files

## 2. Python Environment Standardization

### Current Problem:
- MCP tools use: `/home/opsvi/miniconda/bin/python` (3.12)
- Shell uses: `/home/opsvi/master_root/.venv/bin/python` (3.13)

### Solution Options:

#### Option A: Standardize on Miniconda (Recommended)
```bash
# Update all .mcp.json entries to use miniconda
# Activate miniconda for all shell work
conda activate base
# Install all packages in miniconda
```

#### Option B: Standardize on .venv
```bash
# Update .mcp.json to use .venv Python
# Requires updating all "command" entries in .mcp.json
sed -i 's|/home/opsvi/miniconda/bin/python|/home/opsvi/master_root/.venv/bin/python|g' .mcp.json
```

## 3. Data Migration to KB

### Current:
- Project-intelligence data in `.proj-intel/` files
- ACCF data in `.consult/` files
- Various JSON/YAML scattered

### Target:
- All data in Neo4j knowledge base
- No local file dependencies
- Single source of truth

## 4. Implementation Steps

### Phase 1: Backup (Immediate)
```bash
# Create full backup
tar -czf backup_$(date +%Y%m%d).tar.gz apps/knowledge_system
```

### Phase 2: Environment Fix (Today)
1. Choose Python environment (recommend miniconda)
2. Update .mcp.json
3. Reinstall all packages in chosen environment

### Phase 3: Knowledge System Cleanup (This Week)
1. Move KEEP files to `apps/knowledge_system/core/`
2. Move EVALUATE files to `apps/knowledge_system/advanced/`
3. Archive DELETE files to `.archive/knowledge_experiments/`
4. Update all imports

### Phase 4: Data Migration (Next Week)
1. Run project-intelligence, store in KB
2. Migrate .consult/ data to KB
3. Update all tools to query KB only
4. Remove local file dependencies

## 5. Success Metrics

- [ ] Single Python environment
- [ ] Knowledge system from 61 → ~11 files
- [ ] All data in KB
- [ ] No "module not found" errors
- [ ] Clean project structure

## 6. Risk Mitigation

- Full backup before changes
- Test each change in isolation
- Keep archived code for 30 days
- Document what each deleted file did

## Notes

The autonomous_evolution.py and related files represent sophisticated self-improvement capabilities that should probably be preserved and potentially activated. They're not currently used but represent significant intellectual investment.
