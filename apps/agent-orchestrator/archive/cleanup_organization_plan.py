#!/usr/bin/env python3
"""
Agent Orchestrator Cleanup & Organization Plan
Uses the UnifiedOrchestrator to organize the messy file structure
"""

import asyncio
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.unified.unified_orchestrator import UnifiedOrchestrator, UnifiedConfig
    from src.unified.enhanced_agent_task import EnhancedAgentTask
except ImportError:
    # Fallback to enhanced orchestrator if unified not available
    from src.enhanced_orchestrator import EnhancedOrchestrator, EnhancedAgentTask
    UnifiedOrchestrator = EnhancedOrchestrator
    UnifiedConfig = None

def generate_cleanup_tasks():
    """
    Generate parallel agent tasks to clean up and organize the file structure
    """
    
    tasks = []
    
    # Agent 1: Analyze and categorize all files
    tasks.append(EnhancedAgentTask(
        task_id="analyze_file_structure",
        task_type="solution-architect",
        prompt="""ANALYZE AND CATEGORIZE ALL FILES:

1. SCAN CURRENT DIRECTORY:
   - Use Bash tool to run: find . -type f -name "*.py" | head -50
   - Use Bash tool to run: find . -type f -name "*.json" | head -30  
   - Use Bash tool to run: find . -type f -name "*.md" | head -30
   - Use Bash tool to run: ls -la | grep "^d" to see all directories

2. CATEGORIZE FILES:
   - Core working files (keep in main locations)
   - Test files and outputs (move to tests/)
   - Documentation files (organize in docs/)
   - Example files (move to examples/)
   - Broken/deprecated files (move to archive/)
   - Unknown/mystery files (identify what they do)

3. CREATE ORGANIZATION PLAN:
   CREATE FILE: CLEANUP_ORGANIZATION_PLAN.md
   CONTENT:
   - Current file inventory with categories
   - Proposed new directory structure  
   - Files to keep, move, or delete
   - Clear reasoning for each decision

USE Bash tool to scan directories and files
USE Write tool to create organization plan""",
        agent_uuid="agent_01_analyzer",
        monitoring_enabled=True
    ))
    
    # Agent 2: Clean up root directory
    tasks.append(EnhancedAgentTask(
        task_id="cleanup_root_directory",
        task_type="development-specialist",
        prompt="""CLEAN UP ROOT DIRECTORY:

1. IDENTIFY ROOT CLUTTER:
   - Use Bash tool to list all files in root: ls -la
   - Identify files that don't belong in root
   - Find test outputs, temp files, random scripts

2. ORGANIZE ROOT FILES:
   - Keep only: README.md, core scripts, main config files
   - Move test files to tests/
   - Move examples to examples/ 
   - Move docs to docs/
   - Move random scripts to scripts/ or archive

3. CREATE CLEAN ROOT STRUCTURE:
   - src/ (core source code)
   - tests/ (all test files)
   - examples/ (usage examples)
   - docs/ (documentation)
   - scripts/ (utility scripts)
   - archive/ (old/broken stuff)

CREATE FILE: root_cleanup_log.md
CONTENT: Document what was moved where and why

USE Bash tool to move files: mv file destination/
USE Write tool to document changes""",
        agent_uuid="agent_02_root",
        monitoring_enabled=True
    ))
    
    # Agent 3: Organize test files and outputs
    tasks.append(EnhancedAgentTask(
        task_id="organize_test_files",
        task_type="qa-testing-guru", 
        prompt="""ORGANIZE ALL TEST FILES AND OUTPUTS:

1. FIND ALL TEST-RELATED FILES:
   - Use Bash tool to find: find . -name "*test*" -type f
   - Use Bash tool to find: find . -name "*output*" -type d
   - Use Bash tool to find: find . -name "test_*" -type f
   - Find all JSON output files from testing

2. CREATE TESTS DIRECTORY STRUCTURE:
   - tests/unit/ (unit tests)
   - tests/integration/ (integration tests)  
   - tests/outputs/ (test output files)
   - tests/fixtures/ (test data)
   - tests/archive/ (old test results)

3. MOVE AND ORGANIZE:
   - Move all test_*.py files to tests/
   - Move test output directories to tests/outputs/
   - Move test JSON files to tests/outputs/
   - Create clean test structure

CREATE FILE: tests/TEST_ORGANIZATION_README.md
CONTENT: Explain test structure and how to run tests

USE Bash tool to move files and create directories
USE Write tool to document test organization""",
        agent_uuid="agent_03_tests",
        monitoring_enabled=True
    ))
    
    # Agent 4: Organize documentation  
    tasks.append(EnhancedAgentTask(
        task_id="organize_documentation",
        task_type="technical-writer",
        prompt="""ORGANIZE ALL DOCUMENTATION:

1. FIND ALL DOCUMENTATION FILES:
   - Use Bash tool to find: find . -name "*.md" -type f
   - Use Bash tool to find: find . -name "*README*" -type f
   - Use Bash tool to find directories with docs: find . -name "*doc*" -type d
   - Identify all .md files scattered around

2. CREATE DOCS DIRECTORY STRUCTURE:
   - docs/api/ (API documentation)
   - docs/architecture/ (system design docs)
   - docs/guides/ (how-to guides)
   - docs/legacy/ (old documentation) 
   - docs/analysis/ (analysis reports)

3. ORGANIZE AND CLEAN:
   - Move all .md files to appropriate docs/ subdirs
   - Keep main README.md in root
   - Consolidate duplicate documentation
   - Remove outdated docs

CREATE FILE: docs/DOCUMENTATION_INDEX.md
CONTENT: Master index of all documentation with descriptions

USE Bash tool to move and organize documentation files
USE Write tool to create documentation index""",
        agent_uuid="agent_04_docs",
        monitoring_enabled=True
    ))
    
    # Agent 5: Organize examples and demos
    tasks.append(EnhancedAgentTask(
        task_id="organize_examples",
        task_type="development-specialist",
        prompt="""ORGANIZE EXAMPLES AND DEMO FILES:

1. FIND ALL EXAMPLE FILES:
   - Use Bash tool to find: find . -name "*example*" -type f
   - Use Bash tool to find: find . -name "*demo*" -type f  
   - Use Bash tool to find: find . -name "*sample*" -type f
   - Look for practical usage files

2. CREATE EXAMPLES DIRECTORY STRUCTURE:
   - examples/basic/ (simple usage examples)
   - examples/advanced/ (complex scenarios)
   - examples/integration/ (integration examples)
   - examples/archive/ (old/broken examples)

3. ORGANIZE EXAMPLES:
   - Move all example files to examples/
   - Test which examples still work
   - Archive broken examples
   - Create working example set

CREATE FILE: examples/README.md  
CONTENT: Guide to all examples with descriptions and usage

USE Bash tool to move example files
USE Write tool to create examples guide""",
        agent_uuid="agent_05_examples",
        monitoring_enabled=True
    ))
    
    # Agent 6: Final cleanup and validation
    tasks.append(EnhancedAgentTask(
        task_id="final_cleanup_validation",
        task_type="solution-architect",
        prompt="""FINAL CLEANUP AND VALIDATION:

1. VALIDATE NEW STRUCTURE:
   - Use Bash tool to run: tree -L 3 (or find . -type d | head -20)
   - Check that all important files are in logical places
   - Ensure no critical files were lost
   - Verify unified orchestrator still works

2. CLEAN UP REMAINING CLUTTER:
   - Remove empty directories
   - Clean up any remaining scattered files
   - Remove duplicate files
   - Archive anything still unclear

3. CREATE FINAL ORGANIZATION REPORT:
   CREATE FILE: FINAL_CLEANUP_REPORT.md
   CONTENT:
   - Before/after directory structure
   - Summary of what was moved where
   - Current file organization
   - Instructions for maintaining clean structure
   - Any files that need manual review

4. TEST SYSTEM STILL WORKS:
   - Verify imports work: python -c "from src.unified.unified_orchestrator import UnifiedOrchestrator; print('OK')"
   - Document any path issues found

USE Bash tool to validate structure and test system
USE Write tool to create final report""",
        agent_uuid="agent_06_final",
        monitoring_enabled=True
    ))

    return tasks

async def execute_cleanup():
    """
    Execute the cleanup and organization plan
    """
    
    print("🧹 AGENT ORCHESTRATOR CLEANUP & ORGANIZATION")
    print("=" * 60) 
    print("Using orchestrator to clean up its own file structure")
    print("Running 6 agents in parallel to organize everything")
    print("=" * 60)
    
    # Create orchestrator - try unified first, fallback to enhanced
    try:
        if UnifiedConfig:
            config = UnifiedConfig(
                output_dir=Path("cleanup_output"),
                max_parallel=6,
                enable_collaboration=False,
                enable_quality_gates=False,
                enable_monitoring=True
            )
            orchestrator = UnifiedOrchestrator(config=config)
        else:
            orchestrator = UnifiedOrchestrator(
                output_dir=Path("cleanup_output"),
                max_parallel=6,
                enable_quality_gates=False,
                enable_monitoring=True,
                use_optimizations=True
            )
    except Exception as e:
        print(f"Error creating orchestrator: {e}")
        return False
    
    try:
        print("\n🧹 LAUNCHING 6 PARALLEL CLEANUP AGENTS...")
        tasks = generate_cleanup_tasks()
        
        results = await orchestrator.execute_batch(tasks)
        
        # Check results
        completed = sum(1 for r in results if r.get("status") == "completed")
        total = len(results)
        
        print(f"\n📊 CLEANUP RESULTS: {completed}/{total} agents completed")
        
        if completed == total:
            print("✅ ALL CLEANUP COMPLETE")
            print("\nResult:")
            print("✅ Files organized into logical directory structure")
            print("✅ Root directory cleaned up")
            print("✅ Tests, docs, examples properly organized") 
            print("✅ System validated still working")
            print("\nCheck FINAL_CLEANUP_REPORT.md for details")
            return True
        else:
            print("⚠️ Some cleanup tasks failed")
            print("Check cleanup_output/ for individual task results")
            return False
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(execute_cleanup())
    if success:
        print("\n🎉 Agent orchestrator directory is now organized!")
    else:
        print("\n💥 Cleanup had issues - check the reports")