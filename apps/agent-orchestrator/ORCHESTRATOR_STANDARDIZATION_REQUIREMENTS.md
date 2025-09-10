# Orchestrator Standardization Requirements

**Project Name:** Orchestrator Directory Structure Standardization
**Date:** 2025-09-08
**Priority:** CRITICAL - Immediate implementation required

## Problem Statement

**CRITICAL CHAOS IDENTIFIED**: Multiple concurrent workflows have created a disastrous directory structure with:
- 12+ different output directory systems (`output/`, `outputs/`, `orchestrator_output/`, etc.)
- Complete file intermingling between different workflows
- Failed deliverable placement due to permission issues
- No workflow isolation or identification system

## Evidence of Current Chaos

### Directory Structure Analysis
```
Current chaotic structure:
├── output/                    # Mixed workflow outputs - CHAOS
├── outputs/                   # Analysis workflows
├── orchestrator_output/       # Timestamped workflows
├── test_output/               # Test workflows
├── workflow-results/          # Post-mortem reports
├── web/                       # Dashboard assets
├── docs/                      # Orchestrator documentation (now clean)
├── temp_docs_cleanup/         # Relocated non-orchestrator files
└── [12+ other output directories]
```

### Specific Failure Examples
1. **Session Optimization Workflow**: Intended to create `/apps/session-optimizer/` but wrote to `/output/` due to permission failure
2. **Dashboard Workflow**: Created files scattered across `/output/`, `/web/`, root directory, and `/src/monitoring/`
3. **File Intermingling**: Dashboard, session optimization, and orchestrator files mixed in same directories

## Core Issues Requiring Resolution

### 1. **No Workflow Isolation**
- **Problem**: All workflows dump outputs to shared directories
- **Evidence**: Dashboard and session optimization files mixed in `/output/`
- **Impact**: Impossible to separate workflow deliverables

### 2. **External Directory Permission Failure**
- **Problem**: Agents cannot create directories outside orchestrator path
- **Evidence**: Session optimization fell back from `/apps/session-optimizer/` to `/output/`
- **Root Cause**: Missing `--add-dir /home/opsvi/master_root/apps` parameter
- **Impact**: Projects designed for `/apps/PROJECT-NAME/` fail silently

### 3. **No Project Directory Standards**
- **Problem**: No consistent approach for where different project types create files
- **Evidence**: 12+ different output directory patterns
- **Impact**: Unpredictable file locations, maintenance nightmare

### 4. **Lack of Workflow Identification**
- **Problem**: No way to identify which files belong to which workflow
- **Evidence**: Mixed logs with only timestamps, no workflow names
- **Impact**: Cannot track or monitor concurrent workflows

## Required Standardization

### New Directory Structure Required
```
/home/opsvi/master_root/
├── apps/
│   ├── agent-orchestrator/        # Orchestrator core system
│   │   ├── orchestrator/           # NEW: Standardized orchestrator outputs
│   │   │   ├── workflows/          # All workflow executions
│   │   │   │   ├── active/         # Running workflows
│   │   │   │   │   └── workflow_NAME_ID/
│   │   │   │   │       ├── metadata.json
│   │   │   │   │       ├── orchestrator.log
│   │   │   │   │       ├── agents/
│   │   │   │   │       ├── tasks/
│   │   │   │   │       ├── deliverables/
│   │   │   │   │       └── checkpoints/
│   │   │   │   ├── completed/      # Finished workflows
│   │   │   │   └── failed/         # Failed workflows
│   │   │   └── global/             # System-wide data
│   │   │       ├── registry.json
│   │   │       └── system.log
│   │   ├── docs/                   # Orchestrator operational docs (current)
│   │   └── src/                    # Orchestrator source code (current)
│   ├── dashboard/                  # NEW: Dashboard project
│   │   ├── src/
│   │   ├── web/
│   │   ├── docs/
│   │   └── deliverables/
│   └── session-optimizer/          # NEW: Session optimization project
│       ├── src/
│       ├── analysis/
│       ├── docs/
│       └── deliverables/
```

### Workflow Identification System
- **Naming**: `workflow_{SOURCE}_{TIMESTAMP}_{HASH}`
- **Examples**: `workflow_dashboard-build_20250908_143045_a7f2`
- **Metadata**: JSON files with workflow info, progress, agents, deliverables

### Permission Requirements
- **Add**: `--add-dir /home/opsvi/master_root/apps` to all orchestrator agent commands
- **Enable**: Agents to create project directories outside orchestrator scope
- **Validate**: Proper project directory creation before workflow execution

## Implementation Requirements

### 1. **Immediate Permission Fix**
- Modify `GenericOrchestrator` to add `--add-dir /home/opsvi/master_root/apps` to all agent commands
- Test agents can create `/apps/PROJECT-NAME/` directories successfully
- Validate session optimization workflow can be re-run with proper directory creation

### 2. **Workflow Directory Standardization**
- Implement workflow-specific output directory creation
- Add workflow identification and metadata tracking
- Create global workflow registry for monitoring

### 3. **Project Directory Standards**
- **New projects**: Must create `/apps/PROJECT-NAME/` directories
- **Project deliverables**: Only in project-specific directories
- **Orchestrator operations**: Only in orchestrator-specific directories

### 4. **Backward Compatibility**
- Maintain support for existing command-line interfaces
- Dual-write during transition period (old + new structure)
- Migration utilities for existing workflow data

### 5. **Cleanup and Migration**
- Move misplaced files to correct project directories
- Archive legacy output directories after migration
- Clean separation between orchestrator operations and project deliverables

## Success Criteria

- ✅ Each workflow has isolated output directory
- ✅ Agents can create `/apps/PROJECT-NAME/` directories without permission failure
- ✅ No file intermingling between different workflows
- ✅ Clear separation between orchestrator operations and project deliverables
- ✅ Workflow identification and tracking system functional
- ✅ Dashboard can monitor concurrent workflows effectively
- ✅ All existing command-line interfaces continue working

## Current Background Process Risk

**CRITICAL**: 12+ background orchestrator processes currently running with chaotic structure:
- System analysis workflows
- Resume operations
- WBS documentation
- Apps audit processes

**Risk**: These continue creating mixed outputs while we standardize.
**Recommendation**: Implement fixes immediately to prevent further chaos.

## Reference Documents

- **Current Analysis**: `workflow-results/COMPREHENSIVE_WORKFLOW_ANALYSIS_REPORT.md`
- **Session Optimization Post-mortem**: `workflow-results/session_optimization_phase1_analysis.md`
- **Original Structure Spec**: Created earlier but needs updating based on actual chaos discovered

## Implementation Priority

1. **IMMEDIATE**: Fix agent permissions (`--add-dir` parameter)
2. **URGENT**: Implement workflow isolation for new workflows
3. **HIGH**: Create proper project directories for recent workflows
4. **MEDIUM**: Migrate existing chaotic outputs to standardized structure
5. **LOW**: Archive legacy directories after migration complete

This standardization is critical for the orchestrator dashboard to function effectively and for preventing further chaos from concurrent workflow operations.
