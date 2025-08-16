"""
AI Orchestrator - Master controller where ALL decisions go through AI
Replaces the rule-based agent.py with AI-native intelligence

This is the new entry point that demonstrates how to leverage Claude AI
at every decision point instead of using hardcoded logic.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

# AI-First Components (new)
from src.core.ai_decision_engine import AIDecisionEngine, DecisionType
from src.learning.ai_pattern_engine import AIPatternEngine, PatternType
from src.core.error_recovery import AIErrorRecovery  # To be created
from src.modification.ai_code_generator import AICodeGenerator  # To be created
from src.learning.ai_learning_system import AILearningSystem  # To be created

# Existing components
from src.core.claude_client import ClaudeClient
from src.core.state_manager import StateManager
from src.governance.resource_monitor import ResourceMonitor
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIExecutionContext:
    """Context for AI-driven execution"""

    iteration: int
    goal: str
    current_state: Dict[str, Any]
    patterns_detected: List[Any]
    insights: Dict[str, Any]
    strategy: Dict[str, Any]
    metadata: Dict[str, Any]


class AIOrchestrator:
    """
    Master AI Orchestrator - Everything goes through AI.

    This replaces the traditional AutonomousAgent with an AI-native approach
    where Claude makes ALL decisions instead of using hardcoded rules.

    Key Differences from Traditional Agent:
    - No if/else statements for decisions
    - No string matching or regex patterns
    - No template-based code generation
    - No statistical learning (counts/averages)
    - Everything is semantic AI understanding
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize AI-first orchestrator"""

        self.id = str(uuid.uuid4())[:8]
        self.config = config

        # Core Claude client
        self.claude = ClaudeClient(config.get("claude", {}))

        # AI-First Components (ALL decisions go through these)
        self.decision_engine = AIDecisionEngine(self.claude)
        self.pattern_engine = AIPatternEngine(self.claude)

        # These would be implemented similarly to the examples
        # self.error_recovery = AIErrorRecovery(self.claude)
        # self.code_generator = AICodeGenerator(self.claude)
        # self.learning_system = AILearningSystem(self.claude)

        # State management (minimal, most state is in AI context)
        self.state_manager = StateManager(self.id)

        # Resource monitoring (still needed for safety)
        from src.governance.resource_monitor import ResourceLimits

        limits = config.get("limits", {})
        self.resource_monitor = ResourceMonitor(
            ResourceLimits(
                max_cpu_percent=limits.get("cpu_percent", 80),
                max_memory_mb=limits.get("memory_mb", 2048),
                max_disk_usage_gb=limits.get("disk_gb", 10),
                max_total_tokens=limits.get("daily_tokens", 100000),
            )
        )

        # Execution state
        self.iteration = 0
        self.execution_history = []
        self.current_goal = None
        self.start_time = datetime.now()

    async def run_autonomous_loop(self, initial_goal: str):
        """
        Main autonomous loop - EVERYTHING goes through AI.

        This demonstrates the AI-first approach where Claude makes all decisions.
        No hardcoded logic, no rules, just AI intelligence.
        """

        logger.info(f"AI Orchestrator {self.id} starting with goal: {initial_goal}")
        self.current_goal = initial_goal

        # Initialize with AI assessment
        await self._ai_initialize(initial_goal)

        while await self._ai_should_continue():
            try:
                # Create execution context
                context = AIExecutionContext(
                    iteration=self.iteration,
                    goal=self.current_goal,
                    current_state=await self._get_current_state(),
                    patterns_detected=[],
                    insights={},
                    strategy={},
                    metadata={"timestamp": datetime.now().isoformat()},
                )

                # 1. AI assesses current situation (replaces hardcoded checks)
                assessment = await self._ai_assess_state(context)

                # 2. AI identifies patterns (replaces regex/string matching)
                patterns = await self._ai_detect_patterns(assessment, context)
                context.patterns_detected = patterns

                # 3. AI creates strategy (replaces if/else planning)
                strategy = await self._ai_create_strategy(assessment, patterns, context)
                context.strategy = strategy

                # 4. AI executes strategy with parallel processing
                results = await self._ai_execute_strategy(strategy, context)

                # 5. AI learns from results (replaces statistical counting)
                insights = await self._ai_learn(results, context)
                context.insights = insights

                # 6. AI decides on improvements (replaces template generation)
                improvements = await self._ai_generate_improvements(insights, context)

                # 7. Apply improvements if AI deems beneficial
                if improvements:
                    await self._ai_apply_improvements(improvements, context)

                # 8. AI handles any errors intelligently
                if "errors" in results:
                    await self._ai_handle_errors(results["errors"], context)

                # Record execution
                self.execution_history.append(
                    {
                        "iteration": self.iteration,
                        "assessment": assessment,
                        "patterns": len(patterns),
                        "strategy": strategy.get("approach", ""),
                        "results": results.get("summary", ""),
                        "insights": insights.get("key_learning", ""),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                self.iteration += 1

                # Log progress (AI determines what's important to log)
                await self._ai_log_progress(context)

            except Exception as e:
                # AI handles ALL errors - no hardcoded error handling
                recovery = await self._ai_error_recovery(e, context)
                if not recovery.get("continue", False):
                    break

        # AI creates final summary
        summary = await self._ai_create_summary()
        logger.info(f"AI Orchestrator completed: {summary}")

        return summary

    async def _ai_initialize(self, goal: str):
        """AI-driven initialization"""

        decision = await self.decision_engine.make_decision(
            context={
                "goal": goal,
                "system_state": "initializing",
                "available_resources": await self.resource_monitor.get_current_usage(),
            },
            decision_type=DecisionType.STATE_ASSESSMENT,
            options=None,  # Let AI determine initialization steps
        )

        # Execute AI's initialization plan
        for step in decision.action_plan.get("immediate_steps", []):
            logger.info(f"AI Initialization: {step}")
            # Would execute actual initialization based on AI decision

    async def _ai_should_continue(self) -> bool:
        """AI decides whether to continue execution"""

        decision = await self.decision_engine.make_decision(
            context={
                "goal": self.current_goal,
                "iteration": self.iteration,
                "execution_history": self.execution_history[-5:],  # Recent history
                "resource_usage": await self.resource_monitor.get_current_usage(),
                "time_elapsed": (datetime.now() - self.start_time).total_seconds(),
            },
            decision_type=DecisionType.CONTINUATION,
        )

        # AI decides based on comprehensive analysis, not simple conditions
        return decision.decision == "continue" and decision.confidence > 0.5

    async def _ai_assess_state(self, context: AIExecutionContext) -> Dict[str, Any]:
        """AI assesses current state with deep understanding"""

        decision = await self.decision_engine.make_decision(
            context={
                "goal": context.goal,
                "iteration": context.iteration,
                "current_state": context.current_state,
                "recent_history": self.execution_history[-3:],
            },
            decision_type=DecisionType.STATE_ASSESSMENT,
        )

        return {
            "assessment": decision.decision,
            "reasoning": decision.reasoning,
            "insights": decision.insights,
            "opportunities": decision.insights.get("opportunities_found", []),
            "risks": decision.insights.get("risks_identified", []),
            "confidence": decision.confidence,
        }

    async def _ai_detect_patterns(
        self, assessment: Dict[str, Any], context: AIExecutionContext
    ) -> List[Any]:
        """AI detects patterns using semantic understanding"""

        result = await self.pattern_engine.recognize_patterns(
            data={
                "assessment": assessment,
                "execution_history": self.execution_history[-10:],
                "current_state": context.current_state,
            },
            pattern_type=None,  # Let AI determine pattern types
            depth="deep",
        )

        return result.get("patterns", [])

    async def _ai_create_strategy(
        self, assessment: Dict[str, Any], patterns: List[Any], context: AIExecutionContext
    ) -> Dict[str, Any]:
        """AI creates strategy using strategic reasoning"""

        decision = await self.decision_engine.make_decision(
            context={
                "goal": context.goal,
                "assessment": assessment,
                "patterns": [p.__dict__ if hasattr(p, "__dict__") else p for p in patterns],
                "resources": await self.resource_monitor.get_current_usage(),
                "constraints": self.config.get("constraints", {}),
            },
            decision_type=DecisionType.STRATEGY_SELECTION,
        )

        return {
            "approach": decision.decision,
            "reasoning": decision.reasoning,
            "action_plan": decision.action_plan,
            "confidence": decision.confidence,
            "alternatives": decision.alternatives,
        }

    async def _ai_execute_strategy(
        self, strategy: Dict[str, Any], context: AIExecutionContext
    ) -> Dict[str, Any]:
        """Execute strategy with AI-driven parallel processing"""

        results = {"summary": "", "details": [], "errors": []}

        # Get parallel tasks from strategy
        parallel_tasks = strategy.get("action_plan", {}).get("parallel_tasks", [])

        if parallel_tasks:
            # Execute tasks in parallel using AI
            try:
                # Create batch for parallel execution
                batch_tasks = []
                for task in parallel_tasks:
                    batch_tasks.append(
                        {
                            "task": task,
                            "output_format": "json",
                            "permission_mode": "bypassPermissions",
                        }
                    )

                # Use Claude batch execution
                batch_result = await self.claude.execute_batch(batch_tasks)
                results["details"] = batch_result
                results["summary"] = f"Executed {len(parallel_tasks)} tasks in parallel"

            except Exception as e:
                results["errors"].append(str(e))
                results["summary"] = f"Parallel execution failed: {e}"

        # Execute immediate steps
        immediate_steps = strategy.get("action_plan", {}).get("immediate_steps", [])
        for step in immediate_steps:
            try:
                # Each step goes through AI
                step_result = await self.claude.execute(step, mode="sync")
                results["details"].append(step_result)
            except Exception as e:
                results["errors"].append(f"Step '{step}' failed: {e}")

        return results

    async def _ai_learn(
        self, results: Dict[str, Any], context: AIExecutionContext
    ) -> Dict[str, Any]:
        """AI extracts deep learnings, not statistics"""

        decision = await self.decision_engine.make_decision(
            context={
                "iteration": context.iteration,
                "goal": context.goal,
                "strategy": context.strategy,
                "results": results,
                "patterns": context.patterns_detected,
                "execution_history": self.execution_history[-5:],
            },
            decision_type=DecisionType.LEARNING_EXTRACTION,
        )

        return {
            "key_learning": decision.insights.get("key_observation", ""),
            "patterns_learned": decision.insights.get("patterns_detected", []),
            "improvements_identified": decision.insights.get("opportunities_found", []),
            "predictive_insights": decision.action_plan.get("predictions", []),
            "confidence": decision.confidence,
        }

    async def _ai_generate_improvements(
        self, insights: Dict[str, Any], context: AIExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """AI generates creative improvements, not templates"""

        if not insights.get("improvements_identified"):
            return None

        decision = await self.decision_engine.make_decision(
            context={
                "insights": insights,
                "current_code": "",  # Would load actual code
                "goal": context.goal,
                "patterns": context.patterns_detected,
            },
            decision_type=DecisionType.CODE_GENERATION,
        )

        if decision.confidence < 0.7:
            return None

        return {
            "improvement_type": decision.decision,
            "code": decision.action_plan.get("generated_code", ""),
            "reasoning": decision.reasoning,
            "expected_impact": decision.insights,
        }

    async def _ai_apply_improvements(
        self, improvements: Dict[str, Any], context: AIExecutionContext
    ):
        """Apply AI-generated improvements"""

        logger.info(f"Applying AI improvement: {improvements['improvement_type']}")

        # In production, would actually apply the improvements
        # For now, just log
        logger.info(f"AI Reasoning: {improvements['reasoning']}")
        logger.info(f"Expected Impact: {improvements['expected_impact']}")

    async def _ai_handle_errors(self, errors: List[Any], context: AIExecutionContext):
        """AI handles errors with deep understanding"""

        for error in errors:
            decision = await self.decision_engine.make_decision(
                context={
                    "error": str(error),
                    "error_context": context.__dict__,
                    "execution_history": self.execution_history[-3:],
                },
                decision_type=DecisionType.ERROR_ANALYSIS,
            )

            # Execute AI's recovery strategy
            recovery_plan = decision.action_plan
            logger.info(f"AI Error Recovery: {decision.reasoning}")

            # Apply recovery (in production would execute actual recovery)
            for step in recovery_plan.get("immediate_steps", []):
                logger.info(f"Recovery step: {step}")

    async def _ai_error_recovery(
        self, error: Exception, context: AIExecutionContext
    ) -> Dict[str, Any]:
        """AI-driven error recovery"""

        decision = await self.decision_engine.make_decision(
            context={
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context.__dict__,
                "iteration": context.iteration,
            },
            decision_type=DecisionType.ERROR_ANALYSIS,
        )

        # AI decides whether to continue, retry, or stop
        return {
            "continue": decision.action_plan.get("continue", False),
            "recovery_strategy": decision.action_plan.get("recovery_strategy", ""),
            "reasoning": decision.reasoning,
        }

    async def _ai_log_progress(self, context: AIExecutionContext):
        """AI determines what's important to log"""

        # AI decides what information is worth logging
        decision = await self.decision_engine.make_decision(
            context={
                "iteration": context.iteration,
                "insights": context.insights,
                "patterns": len(context.patterns_detected),
                "strategy_summary": context.strategy.get("approach", ""),
            },
            decision_type=DecisionType.STATE_ASSESSMENT,
            constraints={"log_type": "progress_update"},
        )

        # Log what AI deems important
        if decision.insights.get("key_observation"):
            logger.info(
                f"[Iteration {context.iteration}] AI Insight: {decision.insights['key_observation']}"
            )

    async def _ai_create_summary(self) -> Dict[str, Any]:
        """AI creates comprehensive execution summary"""

        decision = await self.decision_engine.make_decision(
            context={
                "goal": self.current_goal,
                "total_iterations": self.iteration,
                "execution_history": self.execution_history,
                "time_elapsed": (datetime.now() - self.start_time).total_seconds(),
            },
            decision_type=DecisionType.LEARNING_EXTRACTION,
        )

        return {
            "goal": self.current_goal,
            "iterations": self.iteration,
            "key_achievements": decision.insights.get("patterns_detected", []),
            "learnings": decision.insights.get("key_observation", ""),
            "recommendations": decision.action_plan.get("immediate_steps", []),
            "success": decision.confidence > 0.7,
        }

    async def _get_current_state(self) -> Dict[str, Any]:
        """Get current system state"""

        return {
            "iteration": self.iteration,
            "goal": self.current_goal,
            "resource_usage": await self.resource_monitor.get_current_usage(),
            "recent_patterns": len(self.execution_history),
            "time_elapsed": (datetime.now() - self.start_time).total_seconds(),
        }


# Demonstration of AI-First vs Traditional Approach
class ComparisonDemo:
    """
    Side-by-side comparison of traditional vs AI-first approaches
    """

    @staticmethod
    def traditional_decision(data: Dict[str, Any]) -> str:
        """Traditional rule-based decision making"""

        # DON'T DO THIS - Hardcoded rules
        if data.get("error_count", 0) > 5:
            return "stop_execution"
        elif data.get("progress", 0) < 50:
            return "increase_resources"
        elif "timeout" in str(data.get("last_error", "")):
            return "retry_with_backoff"
        else:
            return "continue"

    @staticmethod
    async def ai_first_decision(data: Dict[str, Any], decision_engine: AIDecisionEngine) -> str:
        """AI-first decision making"""

        # DO THIS - Let AI understand and decide
        decision = await decision_engine.make_decision(
            context=data, decision_type=DecisionType.STRATEGY_SELECTION
        )

        # AI provides reasoning, alternatives, and confidence
        # Not just a simple string result
        return decision.decision

    @staticmethod
    def traditional_pattern_matching(text: str) -> bool:
        """Traditional pattern matching"""

        # DON'T DO THIS - Simple string matching
        patterns = ["error", "failed", "exception", "timeout"]
        return any(p in text.lower() for p in patterns)

    @staticmethod
    async def ai_pattern_matching(text: str, pattern_engine: AIPatternEngine) -> Dict[str, Any]:
        """AI semantic pattern matching"""

        # DO THIS - Semantic understanding
        result = await pattern_engine.recognize_patterns(
            data={"text": text}, pattern_type=PatternType.ERROR_PATTERN, depth="deep"
        )

        # AI understands context, not just keywords
        return result

    @staticmethod
    def traditional_error_recovery(error: Exception) -> str:
        """Traditional error recovery"""

        # DON'T DO THIS - Fixed strategies
        if isinstance(error, TimeoutError):
            return "retry_with_exponential_backoff"
        elif isinstance(error, MemoryError):
            return "clear_cache_and_retry"
        else:
            return "log_and_continue"

    @staticmethod
    async def ai_error_recovery(
        error: Exception, decision_engine: AIDecisionEngine
    ) -> Dict[str, Any]:
        """AI error recovery"""

        # DO THIS - AI analyzes root cause
        decision = await decision_engine.make_decision(
            context={
                "error": str(error),
                "error_type": type(error).__name__,
                "traceback": "full_traceback_here",
            },
            decision_type=DecisionType.ERROR_ANALYSIS,
        )

        # AI provides root cause analysis and creative recovery
        return decision.action_plan
