#!/usr/bin/env python3
"""
Intelligent Autonomous Coder - Main Entry Point
Full LLM-driven intelligence with multi-agent collaboration and continuous learning
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import intelligent modules
from modules.intelligent_orchestrator import IntelligentOrchestrator
from modules.llm_request_analyzer import LLMRequestAnalyzer
from modules.dynamic_agent_selector import DynamicAgentSelector
from modules.parallel_executor import ParallelExecutor, ExecutionTask
from modules.continuous_learning_system import ContinuousLearningSystem
from core.base import BuildRequest, BuildResult


class IntelligentAutonomousCoder:
    """
    Main intelligent autonomous coder system
    Fully LLM-driven with multi-agent collaboration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize intelligent system"""
        self.config = config or self._load_default_config()
        
        # Initialize core systems
        self.orchestrator = IntelligentOrchestrator(self.config)
        self.request_analyzer = LLMRequestAnalyzer()
        self.agent_selector = DynamicAgentSelector()
        self.parallel_executor = ParallelExecutor(max_workers=10)
        self.learning_system = ContinuousLearningSystem()
        
        # Metrics
        self.total_builds = 0
        self.successful_builds = 0
        self.total_time = 0.0
        
        logger.info("🧠 Intelligent Autonomous Coder initialized")
    
    async def build(self, description: str, **kwargs) -> BuildResult:
        """
        Build software from natural language description
        Uses full LLM intelligence, no keyword matching
        """
        start_time = datetime.now()
        self.total_builds += 1
        
        logger.info(f"📋 Build request: {description}")
        
        try:
            # Phase 1: Deep Understanding
            logger.info("🔍 Phase 1: LLM-Driven Understanding")
            understanding = await self.request_analyzer.analyze(description)
            logger.info(f"   Intent: {understanding.intent}")
            logger.info(f"   Complexity: {understanding.complexity_level}")
            logger.info(f"   Confidence: {understanding.confidence:.2%}")
            
            # Phase 2: Apply Learning
            logger.info("🎓 Phase 2: Applying Learned Patterns")
            optimizations = self.learning_system.apply_learned_patterns({
                "project_type": understanding.core_purpose,
                "complexity": understanding.complexity_level,
                "requirements": understanding.functional_requirements
            })
            
            if optimizations.get("suggested_architecture"):
                logger.info(f"   Using learned architecture: {optimizations['suggested_architecture']}")
            
            # Phase 3: Agent Selection
            logger.info("🤖 Phase 3: Dynamic Agent Selection")
            selected_agents = await self.agent_selector.select_optimal_agents(understanding)
            logger.info(f"   Selected {len(selected_agents)} specialized agents")
            for agent in selected_agents[:5]:  # Show first 5
                logger.info(f"   - {agent.value}")
            
            # Phase 4: Create Execution Plan
            logger.info("📅 Phase 4: Creating Parallel Execution Plan")
            execution_groups = await self.agent_selector.create_execution_plan(
                selected_agents, understanding
            )
            logger.info(f"   Created {len(execution_groups)} parallel execution groups")
            
            # Phase 5: Prepare Tasks
            tasks = self._create_execution_tasks(execution_groups, understanding)
            
            # Phase 6: Execute with Parallelization
            logger.info("⚡ Phase 5: Parallel Multi-Agent Execution")
            context = {
                "understanding": understanding.__dict__,
                "optimizations": optimizations,
                "timestamp": datetime.now().isoformat()
            }
            
            execution_result = await self.parallel_executor.execute_pipeline(tasks, context)
            
            # Phase 7: Process Results
            logger.info("📦 Phase 6: Processing Results")
            build_result = self._process_execution_results(
                execution_result,
                understanding,
                start_time
            )
            
            # Phase 8: Learn from Execution
            logger.info("📚 Phase 7: Learning from Execution")
            await self.learning_system.learn_from_execution(
                description,
                build_result.__dict__,
                {
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "agents_used": [a.value for a in selected_agents],
                    "parallel_groups": len(execution_groups),
                    "success": build_result.success,
                    **execution_result.get("metrics", {})
                }
            )
            
            if build_result.success:
                self.successful_builds += 1
                logger.info("✅ Build completed successfully!")
            else:
                logger.warning("⚠️ Build completed with issues")
            
            # Report metrics
            self._report_metrics(build_result, execution_result)
            
            return build_result
            
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            
            # Try intelligent recovery
            recovery_strategy = self.learning_system.get_error_recovery_strategy(str(e))
            if recovery_strategy:
                logger.info(f"🔧 Attempting recovery: {recovery_strategy.recovery_method}")
                # Implement recovery (simplified for now)
                pass
            
            return BuildResult(
                success=False,
                project_path=Path(kwargs.get("output_path", "./output")),
                tech_stack={},
                files_created=[],
                execution_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)],
                warnings=[],
                metrics={}
            )
    
    def _create_execution_tasks(self, 
                               execution_groups: List[List['AgentType']], 
                               understanding: 'Understanding') -> List[ExecutionTask]:
        """Create execution tasks from agent groups"""
        tasks = []
        task_counter = 0
        
        for group_index, group in enumerate(execution_groups):
            for agent in group:
                task_counter += 1
                task = ExecutionTask(
                    task_id=f"task_{task_counter}",
                    agent_type=agent.value,
                    description=self._get_agent_task_description(agent, understanding),
                    context={
                        "understanding": understanding.__dict__,
                        "group": group_index
                    },
                    parallel_group=group_index,
                    priority=len(execution_groups) - group_index,  # Earlier groups have higher priority
                    timeout=300  # 5 minutes default
                )
                tasks.append(task)
        
        return tasks
    
    def _get_agent_task_description(self, agent: 'AgentType', understanding: 'Understanding') -> str:
        """Get task description for specific agent"""
        descriptions = {
            "requirements-analyst": f"Analyze and document requirements for: {understanding.core_purpose}",
            "solution-architect": f"Design architecture for: {understanding.core_purpose}",
            "development-specialist": f"Implement core functionality for: {understanding.core_purpose}",
            "qa-testing-guru": f"Create comprehensive test suite for: {understanding.core_purpose}",
            "reviewer-critic": f"Review and critique implementation of: {understanding.core_purpose}",
            "technical-writer": f"Create documentation for: {understanding.core_purpose}",
            "excellence-optimizer": f"Optimize for excellence: {understanding.core_purpose}",
            "research-genius": f"Research best practices for: {understanding.core_purpose}"
        }
        
        return descriptions.get(agent.value, f"Process: {understanding.core_purpose}")
    
    def _process_execution_results(self, 
                                  execution_result: Dict,
                                  understanding: 'Understanding',
                                  start_time: datetime) -> BuildResult:
        """Process execution results into BuildResult"""
        
        # Extract key results
        results = execution_result.get("results", {})
        metrics = execution_result.get("metrics", {})
        
        # Aggregate files created
        files_created = []
        tech_stack = {}
        errors = []
        warnings = []
        
        for task_id, task_result in results.items():
            if isinstance(task_result, dict):
                if "files" in task_result:
                    files_created.extend(task_result["files"])
                if "tech_stack" in task_result:
                    tech_stack.update(task_result["tech_stack"])
                if "error" in task_result:
                    errors.append(task_result["error"])
                if "warnings" in task_result:
                    warnings.extend(task_result.get("warnings", []))
        
        # Create output directory
        output_path = Path("./output") / self._generate_project_name(understanding)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write summary
        summary_path = output_path / "build_summary.json"
        with open(summary_path, "w") as f:
            json.dump({
                "understanding": understanding.__dict__,
                "tech_stack": tech_stack,
                "files_created": files_created,
                "execution_metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        return BuildResult(
            success=len(errors) == 0,
            project_path=output_path,
            tech_stack=tech_stack or self._get_default_tech_stack(understanding),
            files_created=files_created or ["build_summary.json"],
            execution_time=(datetime.now() - start_time).total_seconds(),
            errors=errors,
            warnings=warnings,
            metrics={
                "agents_used": metrics.get("total_tasks", 0),
                "parallel_efficiency": metrics.get("parallel_efficiency", 0),
                "cache_hits": metrics.get("cache_hits", 0),
                "understanding_confidence": understanding.confidence
            }
        )
    
    def _generate_project_name(self, understanding: 'Understanding') -> str:
        """Generate project name from understanding"""
        # Use core purpose for name
        words = understanding.core_purpose.lower().split()[:3]
        name = "-".join(word for word in words if word.isalnum())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}" if name else f"project_{timestamp}"
    
    def _get_default_tech_stack(self, understanding: 'Understanding') -> Dict[str, str]:
        """Get default tech stack based on understanding"""
        if understanding.suggested_technologies:
            return understanding.suggested_technologies
        
        # Intelligent defaults based on patterns
        if "api" in understanding.core_purpose.lower():
            return {
                "framework": "fastapi@0.117.1",
                "language": "python@3.13.1",
                "database": "postgresql@17.2"
            }
        elif "web" in understanding.core_purpose.lower():
            return {
                "framework": "react@19.1.1",
                "bundler": "vite@7.1.1",
                "language": "typescript@5.7.2"
            }
        else:
            return {
                "language": "python@3.13.1"
            }
    
    def _report_metrics(self, build_result: BuildResult, execution_result: Dict):
        """Report execution metrics"""
        metrics = execution_result.get("metrics", {})
        
        logger.info("\n" + "="*60)
        logger.info("📊 EXECUTION METRICS")
        logger.info("="*60)
        logger.info(f"⏱️  Total Time: {build_result.execution_time:.2f}s")
        logger.info(f"🤖 Agents Used: {metrics.get('total_tasks', 0)}")
        logger.info(f"✅ Tasks Completed: {metrics.get('completed', 0)}")
        logger.info(f"❌ Tasks Failed: {metrics.get('failed', 0)}")
        logger.info(f"⚡ Parallel Efficiency: {metrics.get('parallel_efficiency', 'N/A')}")
        logger.info(f"💾 Cache Hits: {metrics.get('cache_hits', 0)}")
        logger.info(f"🔄 Retries: {metrics.get('retries', 0)}")
        logger.info(f"🎯 Understanding Confidence: {build_result.metrics.get('understanding_confidence', 0):.2%}")
        
        # Learning metrics
        learning_report = self.learning_system.get_learning_report()
        logger.info(f"\n📚 LEARNING METRICS")
        logger.info(f"🧠 Patterns Learned: {learning_report['patterns_learned']}")
        logger.info(f"📈 Current Success Rate: {learning_report['improvement_metrics']['current_success_rate']:.2%}")
        logger.info(f"⬆️  Improvement: {learning_report['improvement_metrics'].get('improvement_percentage', 0):.1f}%")
        logger.info("="*60 + "\n")
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "llm": {
                "provider": "claude",  # or "gpt4", "gemini"
                "model": "claude-3-opus",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "execution": {
                "max_parallel_tasks": 10,
                "task_timeout": 300,
                "retry_max": 3,
                "cache_enabled": True
            },
            "learning": {
                "enabled": True,
                "pattern_threshold": 0.7,
                "performance_window": 100
            },
            "agents": {
                "prefer_specialists": True,
                "max_agents": 15,
                "parallel_groups": True
            }
        }
    
    async def interactive_build(self, description: str) -> BuildResult:
        """
        Interactive build with user refinement
        """
        logger.info("🎯 Starting Interactive Build Mode")
        
        # Initial understanding
        understanding = await self.request_analyzer.analyze(description)
        
        # Present understanding for confirmation
        print("\n" + "="*60)
        print("📋 I understand you want to build:")
        print(f"   Purpose: {understanding.core_purpose}")
        print(f"   Users: {', '.join(understanding.target_users)}")
        print(f"   Complexity: {understanding.complexity_level}")
        print(f"   Key Features:")
        for req in understanding.functional_requirements[:5]:
            print(f"   - {req}")
        print("\n   Implied Features (I'll add these):")
        for req in understanding.implied_requirements[:5]:
            print(f"   - {req}")
        print("="*60)
        
        # Get user confirmation
        response = input("\n❓ Does this look correct? (yes/no/refine): ").lower()
        
        if response == "refine":
            refinement = input("📝 What should I adjust? ")
            # Re-analyze with refinement
            understanding = await self.request_analyzer.analyze(f"{description}. {refinement}")
        elif response == "no":
            logger.info("Build cancelled by user")
            return None
        
        # Continue with build
        return await self.build(description)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        learning_report = self.learning_system.get_learning_report()
        
        return {
            "total_builds": self.total_builds,
            "successful_builds": self.successful_builds,
            "success_rate": self.successful_builds / self.total_builds if self.total_builds > 0 else 0,
            "patterns_learned": learning_report["patterns_learned"],
            "error_strategies": learning_report["error_strategies"],
            "improvement": learning_report["improvement_metrics"].get("improvement_percentage", 0),
            "top_patterns": learning_report["top_patterns"]
        }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Intelligent Autonomous Coder - LLM-driven software development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Build a real-time chat application"
  %(prog)s "Create a machine learning API for image classification"
  %(prog)s --interactive "Build a dashboard"
  %(prog)s --stats  # Show learning statistics
        """
    )
    
    parser.add_argument(
        'description',
        nargs='?',
        help='Natural language description of what to build'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode with refinement'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./output',
        help='Output directory'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show system statistics'
    )
    
    parser.add_argument(
        '--config',
        help='Configuration file (JSON)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Initialize system
    coder = IntelligentAutonomousCoder(config)
    
    # Handle different modes
    if args.stats:
        stats = coder.get_system_stats()
        print("\n" + "="*60)
        print("📊 SYSTEM STATISTICS")
        print("="*60)
        print(f"Total Builds: {stats['total_builds']}")
        print(f"Success Rate: {stats['success_rate']:.2%}")
        print(f"Patterns Learned: {stats['patterns_learned']}")
        print(f"Error Strategies: {stats['error_strategies']}")
        print(f"Improvement: {stats['improvement']:.1f}%")
        print("\nTop Patterns:")
        for pattern in stats['top_patterns']:
            print(f"  - {pattern['description']} (success: {pattern['success_rate']:.2%})")
        print("="*60)
        
    elif args.description:
        # Build from description
        if args.interactive:
            result = await coder.interactive_build(args.description)
        else:
            result = await coder.build(args.description, output_path=args.output)
        
        if result and result.success:
            print(f"\n✅ Project created at: {result.project_path}")
            print(f"📄 Files created: {len(result.files_created)}")
            print(f"⏱️  Time: {result.execution_time:.2f}s")
            sys.exit(0)
        else:
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())