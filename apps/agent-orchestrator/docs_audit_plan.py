#!/usr/bin/env python3
"""
Documentation Audit Plan
Comprehensive analysis of the docs/ directory to identify valid, outdated, and misaligned documentation
using the Enhanced Orchestrator with parallel agents for maximum speed.
"""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import List

# Add src to path for orchestrator imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhanced_orchestrator import EnhancedOrchestrator, EnhancedAgentTask


async def execute_docs_audit_plan():
    """
    Execute comprehensive documentation audit using Enhanced Orchestrator
    """
    
    # Setup orchestrator with enhanced features enabled
    output_dir = Path(__file__).parent / "docs_audit_results"
    
    # Load tokens properly using the token loader
    from src.token_loader import load_tokens
    tokens = load_tokens()
    
    if not tokens:
        print("❌ No tokens available from token loader")
        print("Ensure tokens are properly configured")
        return None
    
    print(f"🔑 Loaded {len(tokens)} tokens for parallel execution")
    
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir,
        max_parallel=min(12, len(tokens)),  # Use available tokens, up to 12
        tokens=tokens,  # Use proper token pool
        use_optimizations=True,
        enable_quality_gates=False,  # Keep disabled for this analysis
        enable_monitoring=False,  # Keep disabled for this analysis
        enable_dynamic_configs=True,
        # Dynamic architecture features following working pattern
        master_mcp_registry_path=Path("/home/opsvi/master_root/.claude/master_mcp_registry.json"),
        agent_execution_profile="research",  # Research profile for doc analysis
        agent_debug_mode=False,  # Clean JSON output
        agent_base_work_dir=output_dir / "agent_workspaces",
        log_to_work_dir=True,
    )
    
    def generate_docs_audit_tasks() -> List[EnhancedAgentTask]:
        """Generate comprehensive documentation audit tasks"""
        
        tasks = []
        app_root = Path(__file__).parent
        
        # Phase 1: Directory Structure Analysis (3 parallel agents)
        
        tasks.append(EnhancedAgentTask(
            task_id="docs_structure_inventory",
            task_type="research-genius",
            prompt=f"""
            DOCS STRUCTURE INVENTORY ANALYSIS
            
            Analyze the complete directory structure of: {app_root}/docs/
            
            Your mission:
            1. Create a comprehensive inventory of all files and directories
            2. Categorize files by type (.md, .json, .py, etc.)
            3. Identify directory organization patterns
            4. Note file sizes, modification dates, and naming conventions
            5. Create a structural overview with file counts per directory
            
            Output a detailed JSON report with:
            - Total file counts by type and directory
            - Directory structure tree
            - File metadata (size, modified date, extension)
            - Naming pattern analysis
            - Structural recommendations
            """,
            agent_uuid=str(uuid.uuid4()),
            team_id="structure-analysis",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="structure_analysis"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="docs_content_categorization",
            task_type="research-genius", 
            prompt=f"""
            DOCS CONTENT CATEGORIZATION ANALYSIS
            
            Analyze the content categories within: {app_root}/docs/
            
            Your mission:
            1. Read and categorize all .md files by content type:
               - API documentation
               - User guides
               - Architecture documents
               - Legacy/outdated content
               - Status reports
               - Development notes
            2. Identify which orchestrator version each doc refers to (Generic, Enhanced, Unified)
            3. Find duplicate or overlapping content
            4. Assess content freshness and relevance
            
            Output a detailed categorization report with:
            - Content type breakdown
            - Orchestrator version mapping
            - Duplicate content identification
            - Freshness assessment
            - Category recommendations
            """,
            agent_uuid=str(uuid.uuid4()),
            team_id="content-analysis",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="content_categorization"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="docs_legacy_identification",
            task_type="code-analyzer",
            prompt=f"""
            LEGACY DOCUMENTATION IDENTIFICATION
            
            Deep analysis of legacy and outdated documentation in: {app_root}/docs/
            
            Your mission:
            1. Identify definitively outdated documentation
            2. Find references to non-existent code or features
            3. Locate documentation for removed/archived functionality  
            4. Cross-reference with actual source code in src/
            5. Flag documentation that contradicts current implementation
            
            Special focus on:
            - docs/legacy/ directory contents
            - References to old orchestrator versions
            - Broken internal links
            - Documentation for removed features
            
            CRITICAL REQUIREMENT: NO DELETIONS ALLOWED
            - Only recommend moving files to .archive/ directory
            - Never suggest deleting any documentation
            - Preserve all content for historical reference
            - Create move-to-archive recommendations only
            
            Output a legacy identification report with:
            - Confirmed outdated files list
            - Non-existent feature references
            - Contradiction findings
            - Archive/move recommendations (NO deletions)
            """,
            agent_uuid=str(uuid.uuid4()),
            team_id="legacy-analysis", 
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="legacy_identification"
        ))
        
        # Phase 2: Orchestrator-Specific Analysis (3 parallel agents)
        
        tasks.append(EnhancedAgentTask(
            task_id="generic_orchestrator_docs",
            task_type="code-analyzer",
            prompt=f"""
            GENERIC ORCHESTRATOR DOCUMENTATION ANALYSIS
            
            Analyze documentation specific to the Generic Orchestrator implementation.
            
            Your mission:
            1. Identify all docs that reference the Generic Orchestrator
            2. Cross-reference with actual Generic Orchestrator source code
            3. Validate accuracy of documented features vs actual implementation
            4. Find usage examples and verify they work with current code
            5. Assess completeness of Generic Orchestrator documentation
            
            Source to validate against: {app_root}/src/generic_orchestrator.py
            
            Output a validation report with:
            - Docs specifically about Generic Orchestrator
            - Accuracy assessment for each document
            - Missing documentation areas
            - Code-to-docs alignment status
            - Recommended updates needed
            """,
            dependencies=["docs_structure_inventory"],
            agent_uuid=str(uuid.uuid4()),
            team_id="orchestrator-validation",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="generic_orchestrator_analysis"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="enhanced_orchestrator_docs", 
            task_type="code-analyzer",
            prompt=f"""
            ENHANCED ORCHESTRATOR DOCUMENTATION ANALYSIS
            
            Analyze documentation specific to the Enhanced Orchestrator implementation.
            
            Your mission:
            1. Identify all docs that reference the Enhanced Orchestrator
            2. Cross-reference with actual Enhanced Orchestrator source code  
            3. Validate quality gates, monitoring, and background execution docs
            4. Find usage examples and verify they work with current code
            5. Assess completeness of Enhanced Orchestrator documentation
            
            Source to validate against: {app_root}/src/enhanced_orchestrator.py
            
            Output a validation report with:
            - Docs specifically about Enhanced Orchestrator
            - Feature documentation accuracy (quality gates, monitoring, etc.)
            - Missing documentation areas
            - Code-to-docs alignment status
            - Recommended updates needed
            """,
            dependencies=["docs_structure_inventory"],
            agent_uuid=str(uuid.uuid4()),
            team_id="orchestrator-validation",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="enhanced_orchestrator_analysis"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="unified_orchestrator_docs",
            task_type="code-analyzer", 
            prompt=f"""
            UNIFIED ORCHESTRATOR DOCUMENTATION ANALYSIS
            
            Analyze documentation specific to the Unified Orchestrator implementation.
            
            Your mission:
            1. Identify all docs that reference the Unified Orchestrator
            2. Cross-reference with actual Unified Orchestrator source code
            3. Validate modular feature system and configuration docs
            4. Find usage examples and verify they work with current code
            5. Assess completeness of Unified Orchestrator documentation
            
            Source to validate against: {app_root}/src/unified/unified_orchestrator.py
            
            Output a validation report with:
            - Docs specifically about Unified Orchestrator
            - Feature flag and module system documentation accuracy
            - Missing documentation areas
            - Code-to-docs alignment status
            - Recommended updates needed
            """,
            dependencies=["docs_structure_inventory"],
            agent_uuid=str(uuid.uuid4()),
            team_id="orchestrator-validation",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="unified_orchestrator_analysis"
        ))
        
        # Phase 3: Specialized Content Analysis (3 parallel agents)
        
        tasks.append(EnhancedAgentTask(
            task_id="api_documentation_audit",
            task_type="technical-writer",
            prompt=f"""
            API DOCUMENTATION AUDIT
            
            Comprehensive analysis of API documentation accuracy and completeness.
            
            Your mission:
            1. Analyze all API documentation files
            2. Cross-reference with actual source code APIs
            3. Validate method signatures, parameters, return types
            4. Check for missing API endpoints or methods
            5. Assess documentation quality and usability
            
            Focus areas:
            - docs/api/ directory
            - API_REFERENCE.md files
            - Method documentation in source code
            - Example usage accuracy
            
            Output an API documentation audit with:
            - API documentation accuracy assessment
            - Missing API documentation
            - Outdated method signatures
            - Usability improvements needed
            - Comprehensive API coverage recommendations
            """,
            dependencies=["docs_content_categorization"],
            agent_uuid=str(uuid.uuid4()),
            team_id="specialized-content",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="api_documentation_audit"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="user_guides_validation",
            task_type="technical-writer",
            prompt=f"""
            USER GUIDES VALIDATION AUDIT
            
            Comprehensive validation of user guides and tutorials.
            
            Your mission:
            1. Identify all user guides and tutorials
            2. Test example code and usage instructions
            3. Validate step-by-step procedures
            4. Check for broken links and references
            5. Assess guide completeness and user experience
            
            Focus areas:
            - docs/guides/ directory
            - USAGE_GUIDE.md and similar files
            - Tutorial content
            - Getting started documentation
            
            Output a user guides validation report with:
            - Working vs broken examples
            - Incomplete or unclear instructions
            - Missing prerequisite information
            - User experience assessment
            - Guide improvement recommendations
            """,
            dependencies=["docs_content_categorization"],
            agent_uuid=str(uuid.uuid4()),
            team_id="specialized-content",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="user_guides_validation"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="architecture_docs_analysis",
            task_type="solution-architect",
            prompt=f"""
            ARCHITECTURE DOCUMENTATION ANALYSIS
            
            Deep analysis of architecture documentation accuracy and relevance.
            
            Your mission:
            1. Analyze all architecture documentation
            2. Validate against current system design
            3. Identify outdated architectural decisions
            4. Check for missing architectural documentation
            5. Assess documentation alignment with actual implementation
            
            Focus areas:
            - docs/architecture/ directory
            - System design documents
            - Architecture decision records
            - Component interaction diagrams
            
            Output an architecture documentation analysis with:
            - Current vs documented architecture alignment
            - Outdated architectural decisions
            - Missing architectural documentation
            - Implementation vs design discrepancies
            - Architecture documentation improvement plan
            """,
            dependencies=["docs_content_categorization"],
            agent_uuid=str(uuid.uuid4()),
            team_id="specialized-content",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="architecture_docs_analysis"
        ))
        
        # Phase 4: Final Analysis and Recommendations (3 parallel agents)
        
        tasks.append(EnhancedAgentTask(
            task_id="docs_quality_assessment",
            task_type="reviewer-critic",
            prompt=f"""
            DOCUMENTATION QUALITY ASSESSMENT
            
            Comprehensive quality assessment of all documentation.
            
            Your mission:
            1. Assess writing quality, clarity, and consistency
            2. Check for spelling, grammar, and formatting issues
            3. Evaluate documentation organization and navigation
            4. Identify documentation gaps and overlaps
            5. Rate documentation usefulness for different user types
            
            Consider user types:
            - New developers getting started
            - Experienced developers seeking reference
            - System administrators deploying
            - Contributors wanting to extend functionality
            
            Output a quality assessment report with:
            - Quality ratings by document and category
            - Writing and formatting issues
            - Organization and navigation problems
            - User experience assessment by user type
            - Quality improvement recommendations
            """,
            dependencies=["api_documentation_audit", "user_guides_validation", "architecture_docs_analysis"],
            agent_uuid=str(uuid.uuid4()),
            team_id="final-analysis",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="docs_quality_assessment"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="trusted_docs_index_creation",
            task_type="technical-writer",
            prompt=f"""
            TRUSTED DOCUMENTATION INDEX CREATION
            
            Create a comprehensive index of trusted, accurate documentation.
            
            Your mission:
            1. Compile all validation results from previous analysis
            2. Create a definitive list of accurate, up-to-date documentation
            3. Categorize trusted docs by purpose and audience
            4. Generate a navigation structure for trusted documentation
            5. Create maintenance guidelines for keeping docs current
            
            Based on all previous analysis results, create:
            - TRUSTED_DOCS_INDEX.md - Master index of reliable documentation
            - DOCS_NAVIGATION.md - Organized navigation guide
            - MAINTENANCE_GUIDELINES.md - How to keep docs current
            - DEPRECATION_LIST.md - Files recommended for removal/archival
            
            Output comprehensive documentation organization with:
            - Trusted documentation index
            - Clear categorization and navigation
            - Maintenance procedures
            - Cleanup recommendations
            """,
            dependencies=[
                "generic_orchestrator_docs", "enhanced_orchestrator_docs", "unified_orchestrator_docs",
                "docs_quality_assessment", "docs_legacy_identification"
            ],
            agent_uuid=str(uuid.uuid4()),
            team_id="final-analysis",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="trusted_docs_index"
        ))
        
        tasks.append(EnhancedAgentTask(
            task_id="cleanup_action_plan",
            task_type="business-analyst",
            prompt=f"""
            DOCUMENTATION CLEANUP ACTION PLAN
            
            Create an actionable plan for documentation cleanup and organization.
            
            Your mission:
            1. Synthesize all analysis results into actionable recommendations
            2. Prioritize cleanup actions by impact and effort
            3. Create step-by-step cleanup procedures
            4. Identify documentation that should be immediately removed
            5. Plan for future documentation maintenance
            
            Generate:
            - CLEANUP_ACTION_PLAN.md - Prioritized cleanup steps
            - IMMEDIATE_ACTIONS.md - High-priority items to address first
            - REORGANIZATION_PLAN.md - How to restructure docs directory
            - FUTURE_MAINTENANCE.md - Ongoing documentation management
            
            CRITICAL REQUIREMENT: PRESERVE ALL CONTENT
            - All recommendations must use .archive/ directory for outdated content
            - No deletion of any files - only moves and reorganization
            - Maintain historical documentation for reference
            - Create clear archive organization structure
            
            Output a comprehensive cleanup strategy with:
            - Prioritized move-to-archive actions (NO deletions)
            - Resource requirements and timelines
            - Risk assessment for reorganization actions
            - Success metrics for improved documentation
            - Long-term maintenance strategy with archive management
            """,
            dependencies=[
                "trusted_docs_index_creation", "docs_quality_assessment", 
                "docs_legacy_identification", "docs_content_categorization"
            ],
            agent_uuid=str(uuid.uuid4()),
            team_id="final-analysis",
            validation_required=True,
            quality_gates=[],
            mcp_needs=["shell_exec"],
            work_dir_name="cleanup_action_plan"
        ))
        
        return tasks
    
    # Execute the comprehensive documentation audit
    print("🚀 Starting Comprehensive Documentation Audit")
    print("=" * 80)
    print("Using Enhanced Orchestrator with 12 parallel agents")
    print("Analyzing 86+ files across multiple categories")
    print("Expected completion: ~15-20 minutes with parallel execution")
    print("=" * 80)
    
    result = await orchestrator.run(
        task_generator=generate_docs_audit_tasks,
        result_processor=None
    )
    
    print("\n" + "=" * 80)
    print("📊 DOCUMENTATION AUDIT EXECUTION SUMMARY")
    print("=" * 80)
    print(f"✅ Total tasks: {result['metrics']['total']}")
    print(f"✅ Completed: {result['metrics']['completed']}")
    print(f"❌ Failed: {result['metrics']['failed']}")
    print(f"⏱️ Total duration: {result['metrics'].get('total_duration', 0):.1f}s")
    
    if result['metrics']['completed'] > 0:
        avg_time = result['metrics']['total_duration'] / result['metrics']['completed']
        print(f"📈 Average task time: {avg_time:.1f}s")
    
    # Show quality gate results if available
    if 'quality_status' in result:
        print(f"🔍 Quality gates: {result['quality_status']}")
    
    print(f"\n📁 Results saved to: {output_dir}")
    print("📋 Key deliverables:")
    print("   - TRUSTED_DOCS_INDEX.md (Master index of reliable docs)")
    print("   - CLEANUP_ACTION_PLAN.md (Prioritized cleanup steps)")  
    print("   - Individual analysis reports per orchestrator type")
    print("   - Quality assessment and recommendations")
    
    return result


if __name__ == "__main__":
    asyncio.run(execute_docs_audit_plan())