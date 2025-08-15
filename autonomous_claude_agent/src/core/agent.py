"""
Core Autonomous Agent Implementation
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json

from src.core.claude_client import ClaudeClient, ClaudeTask
from src.core.state_manager import StateManager
from src.core.error_recovery import ErrorRecovery
from src.core.context_manager import ContextManager
from src.capabilities.discovery import CapabilityDiscovery
from src.capabilities.registry import CapabilityRegistry
from src.learning.pattern_engine import PatternEngine
from src.learning.knowledge_base import KnowledgeBase
from src.modification.code_generator import CodeGenerator
from src.research.web_search import WebSearchEngine as ResearchEngine
from src.governance.resource_monitor import ResourceMonitor
from src.governance.safety_rules import SafetyRules
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AgentState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    LEARNING = "learning"
    MODIFYING = "modifying"
    RESEARCHING = "researching"
    ERROR = "error"
    RECOVERING = "recovering"
    SHUTDOWN = "shutdown"

@dataclass
class ExecutionContext:
    """Context for a single execution iteration"""
    iteration: int
    goal: str
    state: AgentState
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)
    checkpoint_id: Optional[str] = None

class AutonomousAgent:
    """Main autonomous agent orchestrator"""
    
    def __init__(self, config: Dict[str, Any], mode: str = "autonomous"):
        self.id = str(uuid.uuid4())[:8]
        self.config = config
        self.mode = mode
        
        # Core components
        self.claude = ClaudeClient(config.get('claude', {}))
        self.state_manager = StateManager(self.id)
        self.error_recovery = ErrorRecovery()
        self.context_manager = ContextManager(config.get('context', {}))
        
        # Capability management
        self.capability_discovery = CapabilityDiscovery()
        self.capability_registry = CapabilityRegistry()
        
        # Learning system
        self.pattern_engine = PatternEngine()
        from pathlib import Path
        self.knowledge_base = KnowledgeBase(Path(f"data/knowledge_{self.id}.db"))
        
        # Self-modification
        self.code_generator = CodeGenerator()
        
        # Research
        self.research_engine = ResearchEngine(config.get('research', {}))
        
        # Governance
        from src.governance.resource_monitor import ResourceLimits
        limits_config = config.get('limits', {})
        resource_limits = ResourceLimits(
            max_cpu_percent=limits_config.get('cpu_percent', 80),
            max_memory_mb=limits_config.get('memory_mb', 2048),
            max_disk_usage_gb=limits_config.get('disk_mb', 1024) / 1024,  # Convert MB to GB
            max_total_tokens=limits_config.get('daily_tokens', 100000)
        )
        self.resource_monitor = ResourceMonitor(resource_limits)
        self.safety_rules = SafetyRules(audit_logger=None)  # Audit logger can be set up separately if needed
        
        # State
        self.current_state = AgentState.INITIALIZING
        self.iteration = 0
        self.max_iterations = config.get('max_iterations', 1000)
        self.current_goal = None
        self.shutdown_requested = False
        self.success_count = 0
        self.error_count = 0
        self.improvements_made = 0
        self.start_time = datetime.now()
        
    async def run(self, initial_goal: str):
        """Main execution loop"""
        logger.info(f"Agent {self.id} starting with goal: {initial_goal}")
        
        try:
            # Initialize
            await self.initialize(initial_goal)
            
            # Main loop
            while self.should_continue():
                context = ExecutionContext(
                    iteration=self.iteration,
                    goal=self.current_goal,
                    state=self.current_state
                )
                
                try:
                    # Check resources
                    if not await self.check_resources():
                        await self.handle_resource_limit()
                        await asyncio.sleep(5)  # Wait before retry
                        continue
                    
                    # Execute iteration
                    result = await self.execute_iteration(context)
                    
                    # Learn from iteration
                    await self.learn_from_iteration(result)
                    
                    # Consider self-modification
                    if await self.should_modify():
                        await self.perform_modification(result)
                    
                    # Save checkpoint periodically
                    if self.iteration % 10 == 0:
                        await self.save_checkpoint(context)
                    
                    self.iteration += 1
                    self.success_count += 1
                    
                    # Log progress
                    if self.iteration % 5 == 0:
                        await self.log_progress()
                    
                except Exception as e:
                    self.error_count += 1
                    await self.handle_error(e, context)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.shutdown()
    
    async def initialize(self, goal: str):
        """Initialize the agent"""
        logger.info("Initializing agent components...")
        
        self.current_goal = goal
        self.current_state = AgentState.IDLE
        
        # Initialize components
        # KnowledgeBase is already initialized in __init__
        await self.capability_discovery.discover_initial_capabilities()
        
        # Load any existing patterns
        # PatternEngine loads patterns in __init__, no separate load needed
        
        # Set up monitoring  
        self.resource_monitor.start_monitoring()  # This is not async
        
        logger.info("Agent initialization complete")
    
    async def execute_iteration(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a single improvement iteration"""
        logger.debug(f"Iteration {context.iteration} starting")
        
        # 1. Assess current state
        self.current_state = AgentState.PLANNING
        assessment = await self.assess_current_state()
        
        # 2. Identify improvements
        opportunities = await self.identify_opportunities(assessment)
        
        # 3. Research if needed
        if opportunities.get('requires_research'):
            self.current_state = AgentState.RESEARCHING
            research = await self.research_solutions(opportunities)
            opportunities['research'] = research
        
        # 4. Create plan
        plan = await self.create_execution_plan(opportunities)
        
        # 5. Execute via Claude
        self.current_state = AgentState.EXECUTING
        execution = await self.execute_with_claude(plan)
        
        # 6. Validate results
        validation = await self.validate_execution(execution)
        
        context.end_time = datetime.now()
        context.metrics = {
            'duration': (context.end_time - context.start_time).total_seconds(),
            'success': validation.get('success', False),
            'improvements': validation.get('improvements', 0)
        }
        
        return {
            'context': context,
            'assessment': assessment,
            'opportunities': opportunities,
            'plan': plan,
            'execution': execution,
            'validation': validation,
            'timestamp': datetime.now()
        }
    
    async def assess_current_state(self) -> Dict[str, Any]:
        """Assess the current state of the system"""
        prompt = f"""
        Assess the current state of the autonomous agent system.
        
        Current goal: {self.current_goal}
        Iteration: {self.iteration}
        Known capabilities: {len(self.capability_registry.capabilities)}
        Learned patterns: {len(self.pattern_engine.patterns)}
        Success rate: {self.success_count / max(1, self.iteration) * 100:.1f}%
        
        Analyze:
        1. Progress toward goal
        2. Current bottlenecks
        3. Missing capabilities
        4. Performance metrics
        
        Return as JSON with structure:
        {{
            "progress": 0-100,
            "bottlenecks": [...],
            "missing_capabilities": [...],
            "metrics": {{...}},
            "recommendations": [...]
        }}
        """
        
        try:
            result = await self.claude.execute(prompt, mode="sync")
            return result
        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            return {
                "progress": 0,
                "bottlenecks": ["assessment_failed"],
                "missing_capabilities": [],
                "metrics": {},
                "recommendations": ["retry_assessment"]
            }
    
    async def identify_opportunities(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Identify improvement opportunities"""
        
        opportunities = {
            'immediate': [],
            'research_needed': [],
            'capabilities_needed': [],
            'requires_research': False
        }
        
        # Check for missing capabilities
        for capability in assessment.get('missing_capabilities', []):
            opportunities['capabilities_needed'].append(capability)
            opportunities['requires_research'] = True
        
        # Check for performance improvements
        if assessment.get('progress', 0) < 50:
            opportunities['immediate'].append('accelerate_progress')
        
        # Check for bottlenecks
        for bottleneck in assessment.get('bottlenecks', []):
            opportunities['immediate'].append(f'resolve_{bottleneck}')
        
        return opportunities
    
    async def research_solutions(self, opportunities: Dict[str, Any]) -> Dict[str, Any]:
        """Research solutions for identified opportunities"""
        
        research_results = {}
        
        for capability in opportunities.get('capabilities_needed', []):
            try:
                results = await self.research_engine.research_capability(capability)
                research_results[capability] = results
            except Exception as e:
                logger.error(f"Research failed for {capability}: {e}")
                research_results[capability] = None
        
        return research_results
    
    async def create_execution_plan(self, opportunities: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan based on opportunities"""
        
        # Determine execution mode
        if len(opportunities.get('immediate', [])) > 3:
            mode = 'batch'
        elif any('complex' in str(o) for o in opportunities.get('immediate', [])):
            mode = 'async'
        else:
            mode = 'sync'
        
        # Create prompt
        prompt = f"""
        Create an execution plan to address these opportunities:
        {json.dumps(opportunities, indent=2)}
        
        Current goal: {self.current_goal}
        
        Provide specific actions to take.
        Return as JSON with structure:
        {{
            "actions": [...],
            "expected_outcomes": [...],
            "success_criteria": {{...}}
        }}
        """
        
        return {
            'type': mode,
            'prompt': prompt,
            'opportunities': opportunities
        }
    
    async def execute_with_claude(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan using Claude Code"""
        
        try:
            # Execute based on plan type
            if plan['type'] == 'batch':
                # Create batch tasks
                tasks = []
                for action in plan.get('actions', [plan['prompt']]):
                    tasks.append(ClaudeTask(prompt=action))
                result = await self.claude.execute_batch(tasks)
                
            elif plan['type'] == 'async':
                # Use async execution
                result = await self.claude.execute(plan['prompt'], mode="async")
                
            else:
                # Use sync execution
                result = await self.claude.execute(plan['prompt'], mode="sync")
            
            return {
                'success': True,
                'result': result,
                'plan': plan
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'plan': plan
            }
    
    async def validate_execution(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution results"""
        
        validation = {
            'success': execution.get('success', False),
            'improvements': 0,
            'issues': []
        }
        
        if not execution.get('success'):
            validation['issues'].append(execution.get('error', 'Unknown error'))
            return validation
        
        # Count improvements
        result = execution.get('result', {})
        if isinstance(result, dict):
            validation['improvements'] = len(result.get('actions', []))
        
        return validation
    
    async def learn_from_iteration(self, result: Dict[str, Any]):
        """Learn from the iteration results"""
        
        self.current_state = AgentState.LEARNING
        
        try:
            # Extract patterns
            patterns = await self.pattern_engine.extract_patterns(result)
            
            # Store in knowledge base
            await self.knowledge_base.store_experience(result)
            
            # Update metrics
            if result['validation'].get('success'):
                self.improvements_made += result['validation'].get('improvements', 0)
            
        except Exception as e:
            logger.error(f"Learning failed: {e}")
    
    async def should_modify(self) -> bool:
        """Determine if self-modification should occur"""
        
        # Only modify every 20 iterations and if we have enough patterns
        if self.iteration % 20 != 0:
            return False
        
        if len(self.pattern_engine.patterns) < 10:
            return False
        
        # Check if modification would be beneficial
        recent_success_rate = self.success_count / max(1, self.iteration)
        return recent_success_rate < 0.8
    
    async def perform_modification(self, result: Dict[str, Any]):
        """Perform self-modification"""
        
        self.current_state = AgentState.MODIFYING
        
        try:
            # Generate improvement code
            improvement = await self.code_generator.generate_improvement(
                patterns=self.pattern_engine.get_top_patterns(5),
                goal=self.current_goal
            )
            
            # Validate improvement
            if await self.code_generator.validate_improvement(improvement):
                # Apply improvement
                await self.code_generator.apply_improvement(improvement)
                self.improvements_made += 1
                logger.info(f"Self-modification applied: {improvement.get('description')}")
            
        except Exception as e:
            logger.error(f"Self-modification failed: {e}")
    
    async def check_resources(self) -> bool:
        """Check if resources are within limits"""
        return await self.resource_monitor.check_all_limits()
    
    async def handle_resource_limit(self):
        """Handle resource limit violations"""
        
        logger.warning("Resource limits exceeded, attempting recovery...")
        
        # Try to free resources
        await self.context_manager.compress_context()
        await self.knowledge_base.cleanup_old_data()
        
        # Garbage collection
        import gc
        gc.collect()
    
    async def handle_error(self, error: Exception, context: ExecutionContext):
        """Handle errors during execution"""
        
        self.current_state = AgentState.ERROR
        logger.error(f"Error in iteration {context.iteration}: {error}")
        
        # Try recovery
        self.current_state = AgentState.RECOVERING
        recovery_success = await self.error_recovery.attempt_recovery(error, context)
        
        if recovery_success:
            self.current_state = AgentState.IDLE
            logger.info("Recovery successful")
        else:
            logger.error("Recovery failed, will retry in next iteration")
            # Save checkpoint for manual intervention
            await self.save_checkpoint(context)
    
    def should_continue(self) -> bool:
        """Determine if agent should continue running"""
        
        if self.shutdown_requested:
            return False
        
        if self.iteration >= self.max_iterations:
            logger.info(f"Max iterations ({self.max_iterations}) reached")
            return False
        
        if self.current_state == AgentState.SHUTDOWN:
            return False
        
        # Stop if too many consecutive errors
        if self.error_count > 10 and self.success_count == 0:
            logger.error("Too many consecutive errors, stopping")
            return False
        
        return True
    
    async def save_checkpoint(self, context: ExecutionContext):
        """Save checkpoint for recovery"""
        
        checkpoint = {
            'agent_id': self.id,
            'iteration': self.iteration,
            'goal': self.current_goal,
            'state': self.current_state.value,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'improvements_made': self.improvements_made,
            'capabilities': await self.capability_registry.export(),
            'patterns': await self.pattern_engine.export(),
            'context': {
                'iteration': context.iteration,
                'goal': context.goal,
                'state': context.state.value,
                'metrics': context.metrics
            },
            'timestamp': datetime.now().isoformat()
        }
        
        checkpoint_id = await self.state_manager.save_checkpoint(checkpoint)
        logger.info(f"Checkpoint saved: {checkpoint_id}")
        return checkpoint_id
    
    async def resume_from_checkpoint(self, checkpoint_id: str, goal: str):
        """Resume from a saved checkpoint"""
        
        logger.info(f"Resuming from checkpoint: {checkpoint_id}")
        
        checkpoint = await self.state_manager.load_checkpoint(checkpoint_id)
        
        # Restore state
        self.iteration = checkpoint['iteration']
        self.current_goal = goal or checkpoint['goal']
        self.success_count = checkpoint['success_count']
        self.error_count = checkpoint['error_count']
        self.improvements_made = checkpoint['improvements_made']
        
        # Restore capabilities and patterns
        await self.capability_registry.import_data(checkpoint['capabilities'])
        await self.pattern_engine.import_data(checkpoint['patterns'])
        
        # Continue execution
        await self.run(self.current_goal)
    
    async def log_progress(self):
        """Log current progress"""
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        success_rate = self.success_count / max(1, self.iteration) * 100
        
        logger.info(f"""
        Progress Report - Agent {self.id}
        =====================================
        Iteration: {self.iteration}/{self.max_iterations}
        Runtime: {runtime:.1f}s
        Success Rate: {success_rate:.1f}%
        Improvements Made: {self.improvements_made}
        Capabilities: {len(self.capability_registry.capabilities)}
        Patterns Learned: {len(self.pattern_engine.patterns)}
        Current Goal: {self.current_goal}
        """)
    
    async def shutdown(self):
        """Graceful shutdown"""
        
        logger.info("Shutting down agent...")
        self.current_state = AgentState.SHUTDOWN
        
        # Save final checkpoint
        await self.save_checkpoint(ExecutionContext(
            iteration=self.iteration,
            goal=self.current_goal,
            state=self.current_state
        ))
        
        # Log final statistics
        await self.log_progress()
        
        # Close connections
        await self.claude.close()
        await self.knowledge_base.close()
        await self.resource_monitor.stop_monitoring()
        
        logger.info(f"Agent {self.id} shutdown complete")

    @property 
    def success_rate(self):
        """Calculate current success rate"""
        if self.iteration == 0:
            return 0
        return self.success_count / self.iteration
    
    @property
    def avg_iteration_time(self):
        """Calculate average iteration time"""
        if self.iteration == 0:
            return 0
        runtime = (datetime.now() - self.start_time).total_seconds()
        return runtime / self.iteration