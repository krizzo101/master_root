# Agent Orchestrator - File Organization Plan

## Current File Inventory

### Core System Files (Keep in Place)
**Main Directory:**
- `main.py` - Primary entry point
- `__init__.py` - Package initialization
- `requirements.txt` - Python dependencies
- `config.json` - System configuration

### Source Code (src/)
**Current State:** Mixed implementation files with different versions
- `unified/` - Latest unified orchestrator implementation
- `enhanced_orchestrator.py` - Enhanced version
- `practical_orchestrator.py` - Practical implementation
- `collaborative_orchestrator.py` - Collaboration features
- `generic_orchestrator.py` - Base implementation
- Multiple subsystems: `collaboration/`, `execution_plan/`, `monitoring/`, `quality_gates/`, `events/`

### Test Files
**Current Location:** Mixed between root and tests/
**Root Level Test Files (TO MOVE):**
- `test_*.py` files (8 files) - Move to `tests/`
- `ep_async_test.py` - Move to `tests/`

**tests/ Directory:**
- `unit/` - Unit tests
- `integration/` - Integration tests  
- `performance/` - Performance tests
- `archive/` - Old test runs

### Example Files
**examples/ Directory:** Well-organized, contains 25 demo files
- Keep as-is, good organization

### Documentation
**docs/ Directory:** Well-structured with subdirectories
- `architecture/` - System design docs
- `collaboration/` - Collaboration system docs
- `legacy/` - Historical documentation
- `guides/` - User guides
- `api/` - API documentation
- `analysis/` - Analysis reports

### Scripts
**scripts/ Directory:** Contains mission and implementation scripts
- `analysis/` - Analysis scripts
- `deployment/` - Deployment scripts
- `monitoring/` - Monitoring scripts
- `testing/` - Testing scripts

### Output Directories (TO CLEAN)
**Multiple output directories from test runs:**
- `cleanup_output/`
- `comprehensive_analysis_output/`
- `consolidation_output/`
- `monitoring_output/`
- `output/`
- `phase1_completion_output/`
- `quick_test_output/`
- `test_*_output/` (12 directories)

### Temporary/Working Files (TO REVIEW)
**Root Level Files:**
- `*_plan.py` files (4 files) - Analysis/planning scripts
- `*_execution_plan.py` files - Execution plan templates
- `*.txt` files (11 files) - Notes and reports
- `collaboration_schemas.json` - Schema definitions
- `results.json` - Test results

### Utility Files
**utils/ Directory:** Helper utilities
- `add_tokens.py` - Token management

## Proposed Directory Structure

```
agent-orchestrator/
├── src/                      # All source code
│   ├── core/                 # Core orchestrator implementations
│   │   ├── unified.py        # Main unified orchestrator
│   │   ├── base.py          # Base classes
│   │   └── interfaces.py    # Interfaces
│   ├── systems/              # Subsystems
│   │   ├── collaboration/   # Collaboration system
│   │   ├── execution/       # Execution planning
│   │   ├── monitoring/      # Monitoring system
│   │   ├── quality/         # Quality gates
│   │   └── events/          # Event system
│   ├── api/                 # API implementations
│   │   ├── web_server.py    
│   │   └── execution_api.py
│   └── utils/               # Utilities
├── tests/                   # All test files
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── performance/        # Performance tests
│   └── fixtures/           # Test fixtures
├── examples/               # Example usage (keep as-is)
├── docs/                   # Documentation (keep structure)
├── scripts/                # Operational scripts
│   ├── analysis/          
│   ├── deployment/        
│   └── testing/           
├── config/                 # Configuration files
│   ├── config.json
│   └── schemas/           # JSON schemas
├── archive/                # Archived/deprecated files
│   ├── old_implementations/
│   ├── test_outputs/      # Old test outputs
│   └── notes/             # Old notes/reports
├── .claude/               # Claude workspace (keep)
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── README.md            # Project readme
```

## Action Plan

### Phase 1: Create Directory Structure
1. Create `src/core/` and `src/systems/` directories
2. Create `src/api/` for API implementations
3. Create `config/` directory for configuration files
4. Create `archive/` directory structure

### Phase 2: Move Core Files
1. Move unified orchestrator to `src/core/unified.py`
2. Move other orchestrator implementations to `src/core/`
3. Consolidate subsystems under `src/systems/`
4. Move API files to `src/api/`

### Phase 3: Consolidate Tests
1. Move all root-level test files to `tests/`
2. Organize by test type (unit/integration/performance)
3. Create fixtures directory for test data

### Phase 4: Archive Old Files
1. Move all `*_output/` directories to `archive/test_outputs/`
2. Move old implementation files to `archive/old_implementations/`
3. Move `.txt` notes to `archive/notes/`
4. Move planning/analysis `.py` files to `archive/planning/`

### Phase 5: Clean Configuration
1. Move `config.json` to `config/`
2. Move schema files to `config/schemas/`
3. Update import paths in affected files

## Files to Delete
- Duplicate/redundant implementations after consolidation
- Empty output directories after archiving
- Temporary test files that are no longer needed

## Files to Keep in Root
- `main.py` - Primary entry point
- `requirements.txt` - Dependencies
- `README.md` - Project documentation
- `__init__.py` - Package initialization
- `.claude/` - Claude workspace

## Reasoning

1. **Separation of Concerns**: Clear separation between source code, tests, documentation, and outputs
2. **Version Management**: Archive old implementations instead of deleting for reference
3. **Test Organization**: Centralize all tests in one location with clear categorization
4. **Output Management**: Archive test outputs to reduce clutter while preserving history
5. **Configuration**: Centralize configuration in dedicated directory
6. **Maintainability**: Clear structure makes it easier to find and maintain code
7. **Scalability**: Structure supports future growth and additions

## Priority Actions

1. **HIGH**: Move test outputs to archive (reduces clutter immediately)
2. **HIGH**: Consolidate test files in tests/ directory
3. **MEDIUM**: Reorganize src/ with clear subsystem structure
4. **LOW**: Move planning/analysis scripts to archive
5. **LOW**: Clean up redundant files after verification

## Notes

- The `.claude/` directory should remain untouched as it's Claude's workspace
- The `examples/` directory is well-organized and should remain as-is
- The `docs/` directory has good structure and should be preserved
- Before deleting any files, ensure they're properly archived or verified as redundant
- Update all import statements after moving files
- Run tests after reorganization to ensure nothing breaks