#!/usr/bin/env python3
"""
Orchestrator Consolidation Execution Plan
Uses the working EnhancedOrchestrator to consolidate all implementations in parallel
"""

import asyncio
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.enhanced_orchestrator import EnhancedOrchestrator, EnhancedAgentTask

def generate_consolidation_tasks():
    """
    Generate 6 parallel agent tasks to consolidate all orchestrator implementations
    """
    
    tasks = []
    
    # Agent 1: Archive broken components & create backup
    tasks.append(EnhancedAgentTask(
        task_id="archive_broken_components",
        task_type="development-specialist",
        prompt="""ARCHIVE BROKEN COMPONENTS:

1. ARCHIVE PracticalOrchestrator (completely broken):
   - Move src/practical_orchestrator.py to src/archived/practical_orchestrator_broken.py
   - Add comment explaining it's missing _execute_task method at line 219
   
2. CREATE WORKING DIRECTORY STRUCTURE:
   - Create src/unified/ directory for new consolidated orchestrator
   - Create src/archived/ directory for broken components
   
3. DELIVERABLE FILES TO CREATE:
   CREATE FILE: src/archived/ARCHIVE_LOG.md
   CONTENT: Document what was archived and why
   
USE Read tool to examine practical_orchestrator.py
USE Write tool to create archive structure
USE Edit tool to move files""",
        agent_uuid="agent_01_archive",
        monitoring_enabled=True
    ))
    
    # Agent 2: Fix token resource leaks
    tasks.append(EnhancedAgentTask(
        task_id="fix_token_resource_leaks",
        task_type="performance-optimizer", 
        prompt="""FIX TOKEN RESOURCE LEAKS:

1. ANALYZE TOKEN USAGE:
   - Read src/generic_orchestrator.py 
   - Read src/enhanced_orchestrator.py
   - Read src/collaborative_orchestrator.py
   - Find all token.acquire() calls without proper try/finally release
   
2. FIX RESOURCE LEAKS:
   - Add try/finally blocks around all token usage
   - Ensure tokens are ALWAYS released even on exceptions
   - Pattern: token = await self.token_pool.acquire(); try: ... finally: self.token_pool.release(token)
   
3. DELIVERABLE FILES TO CREATE:
   CREATE FILE: src/fixes/token_leak_fixes.md
   CONTENT: Document all token leak fixes applied
   
USE Read tool to examine orchestrator files
USE Edit tool to fix token leaks
USE Write tool to document fixes""",
        agent_uuid="agent_02_tokens",
        monitoring_enabled=True
    ))
    
    # Agent 3: Fix EnhancedOrchestrator async issues  
    tasks.append(EnhancedAgentTask(
        task_id="fix_enhanced_orchestrator_async",
        task_type="development-specialist",
        prompt="""FIX ENHANCED ORCHESTRATOR ASYNC ISSUES:

1. FIX ASYNC RACE CONDITION:
   - Read src/enhanced_orchestrator.py line 177
   - Fix quality gates initialization without proper await
   - Add proper error handling for missing imports (AgentStatusMonitor, ExecutionPlan)
   
2. ADD GRACEFUL DEGRADATION:
   - Make all optional imports truly optional with try/except
   - Add fallback behavior when components missing
   - Log warnings but don't crash
   
3. DELIVERABLE FILES TO CREATE:
   CREATE FILE: src/fixes/enhanced_orchestrator_fixes.md
   CONTENT: Document all async and import fixes applied
   
USE Read tool to examine enhanced_orchestrator.py
USE Edit tool to fix async issues and imports  
USE Write tool to document fixes""",
        agent_uuid="agent_03_async",
        monitoring_enabled=True
    ))
    
    # Agent 4: Create UnifiedOrchestrator base
    tasks.append(EnhancedAgentTask(
        task_id="create_unified_orchestrator_base",
        task_type="solution-architect",
        prompt="""CREATE UNIFIED ORCHESTRATOR BASE:

1. DESIGN UNIFIED ARCHITECTURE:
   - Read src/generic_orchestrator.py (working baseline)
   - Read comprehensive_analysis_output/02_enhanced_features_matrix.json
   - Read comprehensive_analysis_output/04_collaboration_capabilities.json
   
2. CREATE UNIFIED ORCHESTRATOR:
   CREATE FILE: src/unified/unified_orchestrator.py
   CONTENT: 
   - Class UnifiedOrchestrator(GenericOrchestrator)
   - Modular feature loading with enable flags
   - Graceful degradation for missing components
   - Feature modules: enhanced, collaboration, quality_gates, monitoring
   
3. CREATE MODULE INTERFACE:
   CREATE FILE: src/unified/orchestrator_module.py  
   CONTENT: Base class for orchestrator feature modules
   
USE Read tool to analyze existing orchestrators
USE Write tool to create unified architecture
USE comprehensive analysis data for feature requirements""",
        agent_uuid="agent_04_unified",
        monitoring_enabled=True
    ))
    
    # Agent 5: Port Enhanced features 
    tasks.append(EnhancedAgentTask(
        task_id="port_enhanced_features",
        task_type="refactoring-master",
        prompt="""PORT ENHANCED FEATURES:

1. EXTRACT WORKING ENHANCED FEATURES:
   - Read src/enhanced_orchestrator.py
   - Extract: UUID tracking, metrics collection, background execution
   - Extract: EnhancedAgentTask class and factory patterns
   - Skip: broken quality gates and monitoring (handle separately)
   
2. CREATE ENHANCED MODULE:
   CREATE FILE: src/unified/modules/enhanced_module.py
   CONTENT:
   - EnhancedFeatureModule class
   - UUID task tracking (100% working)
   - Metrics collection (100% working) 
   - Background execution (100% working)
   - Factory patterns (100% working)
   
3. CREATE ENHANCED TASK:
   CREATE FILE: src/unified/enhanced_agent_task.py
   CONTENT: Enhanced task class with UUID, metadata, validation flags
   
USE Read tool to extract working features
USE Write tool to create modular enhanced features
USE comprehensive analysis to identify working vs broken features""",
        agent_uuid="agent_05_enhanced",
        monitoring_enabled=True
    ))
    
    # Agent 6: Port Collaboration features
    tasks.append(EnhancedAgentTask(
        task_id="port_collaboration_features", 
        task_type="development-specialist",
        prompt="""PORT COLLABORATION FEATURES:

1. EXTRACT COLLABORATION FEATURES:
   - Read src/collaborative_orchestrator.py  
   - Extract: Team formation, message passing, workspace management
   - Extract: 5 execution modes (shared, handoff, review, traditional, hybrid)
   - Extract: 31/35 fully working features from analysis
   
2. CREATE COLLABORATION MODULE:
   CREATE FILE: src/unified/modules/collaboration_module.py
   CONTENT:
   - CollaborationFeatureModule class
   - Team formation with skill matching (100% working)
   - Message bus integration (100% working)
   - Shared workspace creation (100% working)
   - All 5 execution modes (100% working)
   
3. CREATE COLLABORATION CONFIG:
   CREATE FILE: src/unified/collaboration_config.py
   CONTENT: Configuration dataclass for collaboration settings
   
USE Read tool to extract collaboration features
USE Write tool to create modular collaboration system  
USE analysis data showing 31/35 features fully implemented""",
        agent_uuid="agent_06_collaboration",
        monitoring_enabled=True
    ))

    return tasks

async def execute_consolidation():
    """
    Execute orchestrator consolidation using parallel agents
    """
    
    print("🚀 ORCHESTRATOR CONSOLIDATION EXECUTION")
    print("=" * 60)
    print("Using EnhancedOrchestrator to consolidate all implementations")
    print("Running 6 agents in parallel to fix and unify everything")
    print("=" * 60)
    
    # Create orchestrator  
    orchestrator = EnhancedOrchestrator(
        output_dir=Path("consolidation_output"),
        max_parallel=19,
        enable_monitoring=True,
        enable_quality_gates=False,  # Disable broken quality gates
        use_optimizations=True
    )
    
    try:
        # Generate and execute consolidation tasks
        print("\n⚙️ LAUNCHING 6 PARALLEL CONSOLIDATION AGENTS...")
        tasks = generate_consolidation_tasks()
        
        results = await orchestrator.execute_batch(tasks)
        
        # Check results
        completed = sum(1 for r in results if r.get("status") == "completed")
        total = len(results)
        
        print(f"\n📊 CONSOLIDATION RESULTS: {completed}/{total} agents completed")
        
        if completed == total:
            print("✅ ALL CONSOLIDATION COMPLETE")
            print("\nNext steps:")
            print("1. Review generated unified orchestrator in src/unified/")
            print("2. Test the new UnifiedOrchestrator")
            print("3. Update examples to use unified implementation")
            return True
        else:
            print("⚠️ Some consolidation tasks failed")
            print("Check consolidation_output/ for individual task results")
            return False
            
    except Exception as e:
        print(f"❌ Consolidation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(execute_consolidation())
    if success:
        print("\n🎉 Ready to test the unified orchestrator!")
    else:
        print("\n💥 Check the backup: src_backup_* and git log")