#!/usr/bin/env python3
"""
Intelligent Autonomous Coder - Production Implementation
Full LLM intelligence with multi-agent collaboration
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import new intelligent modules
from modules.intelligent_orchestrator import (
    IntelligentOrchestrator,
    Understanding,
    AgentTask,
    AgentType
)
from modules.multi_agent_framework import (
    MultiAgentCollaborationFramework,
    ConsultSuiteAgent,
    ClaudeCodeAgent,
    GeminiAgent,
    ResearchAgent,
    CollaborationResult
)
from core.base import BuildRequest, BuildResult, ProjectType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntelligentAutonomousCoder:
    """
    Production-ready intelligent autonomous coder
    Uses full LLM intelligence and multi-agent collaboration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the intelligent system"""
        self.config = config or {}
        
        # Initialize core systems
        self.orchestrator = IntelligentOrchestrator(config)
        self.collaboration_framework = MultiAgentCollaborationFramework()
        
        # Create and register agents
        self.agents = self.collaboration_framework.create_standard_agents()
        
        # Metrics tracking
        self.metrics = {
            'total_projects': 0,
            'successful_projects': 0,
            'average_time': 0,
            'agent_performance': {},
            'learning_improvements': []
        }
        
        logger.info("🚀 Intelligent Autonomous Coder initialized with %d agents", len(self.agents))
    
    async def create_project(
        self,
        description: str,
        output_path: Optional[Path] = None,
        constraints: Optional[Dict] = None,
        preferences: Optional[Dict] = None
    ) -> BuildResult:
        """
        Create a complete software project from natural language description
        
        Args:
            description: Natural language project description
            output_path: Where to generate the project
            constraints: Technical/business constraints
            preferences: Technology preferences
            
        Returns:
            BuildResult with complete project artifacts
        """
        start_time = datetime.now()
        self.metrics['total_projects'] += 1
        
        logger.info("=" * 80)
        logger.info("🎯 NEW PROJECT REQUEST")
        logger.info("Description: %s", description[:200] + "..." if len(description) > 200 else description)
        logger.info("=" * 80)
        
        # Create build request
        request = BuildRequest(
            description=description,
            output_path=output_path or Path("output"),
            config={
                'constraints': constraints or {},
                'preferences': preferences or {},
                'timestamp': datetime.now().isoformat(),
                'intelligent_mode': True
            }
        )
        
        try:
            # Execute with intelligent orchestrator
            result = await self.orchestrator.build(request)
            
            if result.success:
                self.metrics['successful_projects'] += 1
                logger.info("✅ Project created successfully!")
                logger.info("📁 Location: %s", result.project_path)
                logger.info("📊 Files created: %d", len(result.files_created))
                logger.info("⏱️ Time taken: %.2f seconds", result.execution_time)
                
                # Update metrics
                self.update_metrics(result)
                
                # Display summary
                self.display_summary(result)
            else:
                logger.error("❌ Project creation failed")
                logger.error("Errors: %s", result.errors)
            
            return result
            
        except Exception as e:
            logger.error("💥 Unexpected error: %s", str(e))
            return BuildResult(
                success=False,
                project_path=request.output_path,
                tech_stack={},
                files_created=[],
                execution_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)],
                warnings=[],
                metrics={'error': str(e)}
            )
    
    async def create_with_refinement(
        self,
        description: str,
        max_iterations: int = 3
    ) -> BuildResult:
        """
        Create project with iterative refinement based on quality checks
        """
        logger.info("🔄 Starting iterative project creation with refinement")
        
        result = None
        for iteration in range(max_iterations):
            logger.info(f"Iteration {iteration + 1}/{max_iterations}")
            
            # Create or refine project
            if iteration == 0:
                result = await self.create_project(description)
            else:
                # Get refinement suggestions from quality analysis
                refinements = await self.analyze_and_suggest_refinements(result)
                if not refinements:
                    logger.info("✨ Project meets quality standards!")
                    break
                
                # Apply refinements
                result = await self.apply_refinements(result, refinements)
            
            # Check if result is satisfactory
            if result.success and not result.warnings:
                break
        
        return result
    
    async def analyze_and_suggest_refinements(self, result: BuildResult) -> List[Dict]:
        """
        Analyze project and suggest refinements
        """
        refinements = []
        
        # Use code analyzer agent to review
        analysis_task = {
            'task_id': 'refinement_analysis',
            'agent_id': 'code_analyzer',
            'description': 'Analyze project for improvements',
            'prompt': f"Analyze this project and suggest improvements: {result.project_path}",
            'context': {'project_path': str(result.project_path)}
        }
        
        # Execute analysis
        collaboration_result = await self.collaboration_framework.collaborate([analysis_task])
        
        if collaboration_result.success and collaboration_result.agent_outputs:
            # Extract refinement suggestions
            for output in collaboration_result.agent_outputs.values():
                if output and 'suggestions' in output:
                    refinements.extend(output['suggestions'])
        
        return refinements
    
    async def apply_refinements(self, result: BuildResult, refinements: List[Dict]) -> BuildResult:
        """
        Apply refinements to existing project
        """
        logger.info("📝 Applying %d refinements", len(refinements))
        
        # Create refinement tasks for agents
        tasks = []
        for i, refinement in enumerate(refinements):
            tasks.append({
                'task_id': f'refinement_{i}',
                'agent_id': 'dev_specialist',
                'description': refinement.get('description', 'Apply refinement'),
                'prompt': refinement.get('prompt', ''),
                'context': {
                    'project_path': str(result.project_path),
                    'refinement': refinement
                }
            })
        
        # Execute refinements
        collaboration_result = await self.collaboration_framework.collaborate(tasks)
        
        # Update result with refinements
        if collaboration_result.success:
            result.warnings = []  # Clear warnings after refinement
            result.metrics['refinements_applied'] = len(refinements)
        
        return result
    
    async def batch_create_projects(
        self,
        project_descriptions: List[str],
        parallel: bool = True
    ) -> List[BuildResult]:
        """
        Create multiple projects in batch
        """
        logger.info("📦 Batch creating %d projects (parallel=%s)", 
                   len(project_descriptions), parallel)
        
        if parallel:
            # Create all projects in parallel
            tasks = [
                self.create_project(desc, output_path=Path(f"output/project_{i}"))
                for i, desc in enumerate(project_descriptions)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = BuildResult(
                        success=False,
                        project_path=Path(f"output/project_{i}"),
                        tech_stack={},
                        files_created=[],
                        execution_time=0,
                        errors=[str(result)],
                        warnings=[],
                        metrics={}
                    )
        else:
            # Create projects sequentially
            results = []
            for i, desc in enumerate(project_descriptions):
                result = await self.create_project(
                    desc,
                    output_path=Path(f"output/project_{i}")
                )
                results.append(result)
        
        # Summary statistics
        successful = sum(1 for r in results if r.success)
        logger.info("Batch complete: %d/%d successful", successful, len(results))
        
        return results
    
    def update_metrics(self, result: BuildResult):
        """Update system metrics based on result"""
        # Update average time
        total_time = self.metrics['average_time'] * (self.metrics['successful_projects'] - 1)
        total_time += result.execution_time
        self.metrics['average_time'] = total_time / self.metrics['successful_projects']
        
        # Track agent performance
        if 'agents_used' in result.metrics:
            for agent in result.metrics.get('agent_list', []):
                if agent not in self.metrics['agent_performance']:
                    self.metrics['agent_performance'][agent] = {
                        'uses': 0,
                        'successes': 0
                    }
                self.metrics['agent_performance'][agent]['uses'] += 1
                if result.success:
                    self.metrics['agent_performance'][agent]['successes'] += 1
        
        # Track learning improvements
        if 'learning_entries' in result.metrics:
            self.metrics['learning_improvements'].append({
                'timestamp': datetime.now().isoformat(),
                'entries': result.metrics['learning_entries'],
                'confidence': result.metrics.get('confidence', 0)
            })
    
    def display_summary(self, result: BuildResult):
        """Display project creation summary"""
        print("\n" + "=" * 80)
        print("📊 PROJECT CREATION SUMMARY")
        print("=" * 80)
        print(f"✅ Success: {result.success}")
        print(f"📁 Location: {result.project_path}")
        print(f"📝 Files Created: {len(result.files_created)}")
        print(f"⏱️ Time: {result.execution_time:.2f} seconds")
        
        if result.tech_stack:
            print("\n🛠️ Technology Stack:")
            for category, tech in result.tech_stack.items():
                print(f"  • {category}: {tech}")
        
        if result.metrics:
            print("\n📈 Metrics:")
            for key, value in result.metrics.items():
                if key not in ['error_context', 'agent_list']:
                    print(f"  • {key}: {value}")
        
        if result.warnings:
            print("\n⚠️ Warnings:")
            for warning in result.warnings[:5]:  # Show first 5 warnings
                print(f"  • {warning}")
        
        if result.errors:
            print("\n❌ Errors:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  • {error}")
        
        print("=" * 80 + "\n")
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            'total_projects': self.metrics['total_projects'],
            'successful_projects': self.metrics['successful_projects'],
            'success_rate': (
                self.metrics['successful_projects'] / self.metrics['total_projects']
                if self.metrics['total_projects'] > 0 else 0
            ),
            'average_time': self.metrics['average_time'],
            'agent_performance': self.metrics['agent_performance'],
            'total_agents': len(self.agents),
            'learning_entries': len(self.metrics['learning_improvements'])
        }


async def main():
    """Main execution function with examples"""
    
    # Initialize the intelligent coder
    coder = IntelligentAutonomousCoder()
    
    # Example 1: Simple web application
    print("\n🎯 Example 1: Creating a simple web application")
    result1 = await coder.create_project(
        description="Create a modern React dashboard with user authentication, real-time data visualization using charts, and a responsive design. Include a backend API with Node.js and MongoDB.",
        output_path=Path("output/react-dashboard")
    )
    
    # Example 2: REST API with database
    print("\n🎯 Example 2: Creating a REST API")
    result2 = await coder.create_project(
        description="Build a RESTful API for a task management system with CRUD operations, user authentication, task assignment, due dates, and priority levels. Use FastAPI with PostgreSQL.",
        output_path=Path("output/task-api"),
        preferences={'language': 'python', 'framework': 'fastapi'}
    )
    
    # Example 3: CLI tool
    print("\n🎯 Example 3: Creating a CLI tool")
    result3 = await coder.create_project(
        description="Create a command-line tool for analyzing git repositories. It should show commit statistics, contributor rankings, code churn analysis, and generate reports in multiple formats.",
        output_path=Path("output/git-analyzer"),
        constraints={'max_dependencies': 5}
    )
    
    # Example 4: Project with refinement
    print("\n🎯 Example 4: Creating project with automatic refinement")
    result4 = await coder.create_with_refinement(
        description="Build a real-time chat application with WebSocket support, message history, user presence indicators, and file sharing capabilities.",
        max_iterations=2
    )
    
    # Example 5: Batch project creation
    print("\n🎯 Example 5: Batch creating multiple projects")
    batch_descriptions = [
        "Create a simple todo list web app with local storage",
        "Build a weather forecast CLI tool using a public API",
        "Develop a markdown to HTML converter library"
    ]
    batch_results = await coder.batch_create_projects(
        batch_descriptions,
        parallel=True
    )
    
    # Display final metrics
    print("\n" + "=" * 80)
    print("📊 SYSTEM METRICS")
    print("=" * 80)
    metrics = coder.get_system_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    print("=" * 80)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())