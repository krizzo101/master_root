"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See workflow_intelligence_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)

from typing import List, Any, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from statistics import mean, median
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics"""

    workflow_name: str
    execution_time: float
    success_rate: float
    step_count: int
    failure_points: List[str]
    resource_usage: Dict[str, Any]
    timestamp: datetime


@dataclass
class OptimizationPattern:
    """Identified optimization pattern"""

    pattern_type: str
    description: str
    impact_score: float
    frequency: int
    recommendation: str


class WorkflowIntelligencePlugin(BasePlugin):
    """
    Analyzes workflow execution patterns and provides optimization insights.
    Learns from execution history to improve future performance.
    """

    def __init__(self):
        super().__init__()
        self.execution_history: List[WorkflowMetrics] = []
        self.optimization_patterns: List[OptimizationPattern] = []
        self.learning_enabled = True

    @staticmethod
    def get_name() -> str:
        return "workflow_intelligence"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize workflow intelligence."""
        self.event_bus = event_bus
        self.learning_enabled = config.config.get("learning_enabled", True)

        # Load historical data if available
        historical_data = config.config.get("historical_data", {})
        if historical_data:
            self._load_historical_data(historical_data)

        print(
            f"Workflow Intelligence initialized with learning {'enabled' if self.learning_enabled else 'disabled'}"
        )

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute workflow intelligence operations."""
        try:
            params = context.state
            # Handle both 'action' and 'operation' parameters for backward compatibility
            action = params.get("action") or params.get("operation", "analyze")

            # Handle specific operations used by cognitive enhancement
            if action == "optimize_decision_process":
                return await self._optimize_decision_process(params)
            elif action == "analyze_workflow":
                return await self._analyze_workflow(params)
            elif action == "analyze":
                return await self._analyze_workflow(params)
            elif action == "record_execution":
                return await self._record_execution(params)
            elif action == "get_insights":
                return await self._get_insights(params)
            elif action == "predict_performance":
                return await self._predict_performance(params)
            elif action == "identify_patterns":
                return await self._identify_patterns(params)
            elif action == "recommend_optimizations":
                return await self._recommend_optimizations(params)
            elif action == "benchmark_workflow":
                return await self._benchmark_workflow(params)
            else:
                return PluginResult(
                    success=False, error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Workflow intelligence error: {str(e)}"
            )

    async def _optimize_decision_process(self, params: Dict[str, Any]) -> PluginResult:
        """Optimize decision-making process using workflow intelligence."""
        decision_context = params.get("decision_context", {})

        # Extract decision parameters for analysis
        decision_options = decision_context.get("decision_options", [])
        constraints = decision_context.get("constraints", [])
        budget_context = decision_context.get("budget_context", {})

        # Analyze decision complexity
        complexity_score = len(decision_options) * 0.3 + len(constraints) * 0.2 + 0.5
        if complexity_score > 2.0:
            complexity_level = "high"
        elif complexity_score > 1.0:
            complexity_level = "medium"
        else:
            complexity_level = "low"

        # Generate optimization recommendations
        recommendations = []
        optimization_analysis = {
            "decision_complexity": {
                "level": complexity_level,
                "score": complexity_score,
                "factors": {
                    "option_count": len(decision_options),
                    "constraint_count": len(constraints),
                    "budget_complexity": "high" if budget_context else "low",
                },
            },
            "process_optimization": {},
            "recommendations": recommendations,
        }

        # Complexity-based recommendations
        if complexity_level == "high":
            recommendations.extend(
                [
                    "Break down decision into smaller sub-decisions",
                    "Use structured decision framework (e.g., decision matrix)",
                    "Conduct stakeholder analysis for complex decisions",
                    "Consider pilot testing before full implementation",
                ]
            )
        elif complexity_level == "medium":
            recommendations.extend(
                [
                    "Apply systematic comparison of options",
                    "Document decision criteria and weights",
                    "Validate assumptions before deciding",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Quick decision possible with standard analysis",
                    "Focus on key success factors",
                ]
            )

        # Constraint-specific optimization
        if constraints:
            constraint_analysis = {}
            for i, constraint in enumerate(constraints):
                if isinstance(constraint, str):
                    constraint_type = "unknown"
                    if "budget" in constraint.lower() or "cost" in constraint.lower():
                        constraint_type = "financial"
                    elif "time" in constraint.lower():
                        constraint_type = "temporal"
                    elif "resource" in constraint.lower():
                        constraint_type = "resource"

                    constraint_analysis[f"constraint_{i+1}"] = {
                        "description": constraint,
                        "type": constraint_type,
                        "optimization_approach": self._get_constraint_optimization(
                            constraint_type
                        ),
                    }

            optimization_analysis["process_optimization"][
                "constraint_handling"
            ] = constraint_analysis
            recommendations.append(
                "Address constraints systematically using type-specific approaches"
            )

        # Option analysis optimization
        if decision_options:
            option_patterns = self._analyze_option_patterns(decision_options)
            optimization_analysis["process_optimization"][
                "option_analysis"
            ] = option_patterns

            if option_patterns["has_cost_tradeoffs"]:
                recommendations.append(
                    "Use cost-benefit analysis for options with different cost profiles"
                )
            if option_patterns["has_time_tradeoffs"]:
                recommendations.append(
                    "Consider time-value tradeoffs in decision framework"
                )

        # Historical performance recommendations
        similar_decisions = self._find_similar_decisions(decision_context)
        if similar_decisions:
            optimization_analysis["process_optimization"][
                "historical_insights"
            ] = similar_decisions
            recommendations.append("Apply lessons learned from similar decisions")

        return PluginResult(success=True, data=optimization_analysis)

    def _get_constraint_optimization(self, constraint_type: str) -> str:
        """Get optimization approach for specific constraint type."""
        optimizations = {
            "financial": "Prioritize cost-effective options and consider budget reallocation",
            "temporal": "Focus on time-critical path and parallel processing opportunities",
            "resource": "Optimize resource allocation and consider alternative resources",
            "unknown": "Analyze constraint impact and develop mitigation strategies",
        }
        return optimizations.get(constraint_type, optimizations["unknown"])

    def _analyze_option_patterns(self, options: List[str]) -> Dict[str, Any]:
        """Analyze patterns in decision options."""
        option_text = " ".join(options).lower()

        return {
            "has_cost_tradeoffs": any(
                word in option_text for word in ["expensive", "cheap", "cost", "budget"]
            ),
            "has_time_tradeoffs": any(
                word in option_text for word in ["fast", "slow", "quick", "time"]
            ),
            "has_quality_tradeoffs": any(
                word in option_text for word in ["quality", "performance", "reliable"]
            ),
            "option_diversity": (
                "high" if len(set(options)) == len(options) else "medium"
            ),
        }

    def _find_similar_decisions(
        self, decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find similar historical decisions for insights."""
        # For now, return basic insights - in a real system this would query historical data
        return {
            "similar_decision_count": len(self.execution_history)
            // 3,  # Rough estimate
            "success_rate": 0.8,  # Placeholder
            "common_pitfalls": [
                "Insufficient constraint analysis",
                "Overlooking implementation costs",
                "Not considering long-term implications",
            ],
            "best_practices": [
                "Document decision rationale",
                "Set success metrics before implementation",
                "Plan for decision reversal if needed",
            ],
        }

    async def _analyze_workflow(self, params: Dict[str, Any]) -> PluginResult:
        """Analyze workflow performance and characteristics."""
        workflow_definition = params.get("workflow_definition", {})
        execution_data = params.get("execution_data", {})

        # Basic workflow analysis
        step_count = len(workflow_definition.get("steps", []))
        complexity_score = self._calculate_complexity(workflow_definition)
        estimated_duration = self._estimate_duration(workflow_definition)
        risk_factors = self._identify_risk_factors(workflow_definition)

        # Historical comparison if available
        historical_performance = self._get_historical_performance(
            workflow_definition.get("name", "unknown")
        )

        analysis = {
            "workflow_characteristics": {
                "step_count": step_count,
                "complexity_score": complexity_score,
                "estimated_duration_seconds": estimated_duration,
                "risk_factors": risk_factors,
            },
            "historical_performance": historical_performance,
            "optimization_opportunities": self._identify_optimization_opportunities(
                workflow_definition
            ),
            "success_probability": self._estimate_success_probability(
                workflow_definition
            ),
        }

        return PluginResult(
            success=True,
            data={
                "workflow_analysis": analysis,
                "recommendations": self._generate_recommendations(analysis),
            },
        )

    async def _record_execution(self, params: Dict[str, Any]) -> PluginResult:
        """Record workflow execution for learning."""
        if not self.learning_enabled:
            return PluginResult(
                success=True,
                data={"message": "Learning disabled, execution not recorded"},
            )

        workflow_name = params.get("workflow_name")
        execution_time = params.get("execution_time", 0.0)
        success = params.get("success", False)
        step_results = params.get("step_results", [])
        resource_usage = params.get("resource_usage", {})

        # Calculate metrics
        step_count = len(step_results)
        failure_points = [
            f"step_{i}"
            for i, result in enumerate(step_results)
            if not result.get("success", True)
        ]

        # Create metrics record
        metrics = WorkflowMetrics(
            workflow_name=workflow_name,
            execution_time=execution_time,
            success_rate=1.0 if success else 0.0,
            step_count=step_count,
            failure_points=failure_points,
            resource_usage=resource_usage,
            timestamp=datetime.now(),
        )

        # Store in history
        self.execution_history.append(metrics)

        # Maintain reasonable history size
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]

        # Update patterns if enough data
        if len(self.execution_history) >= 10:
            await self._update_patterns()

        return PluginResult(
            success=True,
            data={
                "recorded_metrics": asdict(metrics),
                "total_executions_recorded": len(self.execution_history),
                "learning_active": True,
            },
        )

    async def _get_insights(self, params: Dict[str, Any]) -> PluginResult:
        """Get workflow execution insights."""
        workflow_name = params.get("workflow_name")
        time_period_days = params.get("time_period_days", 30)

        # Filter data by workflow and time period
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        relevant_executions = [
            m
            for m in self.execution_history
            if (not workflow_name or m.workflow_name == workflow_name)
            and m.timestamp >= cutoff_date
        ]

        if not relevant_executions:
            return PluginResult(
                success=True,
                data={
                    "insights": {"message": "No execution data available for analysis"},
                    "data_points": 0,
                },
            )

        # Calculate insights
        insights = {
            "execution_summary": {
                "total_executions": len(relevant_executions),
                "success_rate": mean([m.success_rate for m in relevant_executions]),
                "average_execution_time": mean(
                    [m.execution_time for m in relevant_executions]
                ),
                "median_execution_time": median(
                    [m.execution_time for m in relevant_executions]
                ),
            },
            "performance_trends": self._analyze_trends(relevant_executions),
            "common_failure_points": self._analyze_failure_points(relevant_executions),
            "resource_utilization": self._analyze_resource_usage(relevant_executions),
            "optimization_patterns": [asdict(p) for p in self.optimization_patterns],
        }

        return PluginResult(
            success=True,
            data={
                "insights": insights,
                "data_points": len(relevant_executions),
                "analysis_period_days": time_period_days,
            },
        )

    async def _predict_performance(self, params: Dict[str, Any]) -> PluginResult:
        """Predict workflow performance based on historical data."""
        workflow_definition = params.get("workflow_definition", {})
        workflow_name = workflow_definition.get("name", "unknown")

        # Get historical data for similar workflows
        similar_executions = [
            m
            for m in self.execution_history
            if m.workflow_name == workflow_name
            or m.step_count == len(workflow_definition.get("steps", []))
        ]

        if not similar_executions:
            return PluginResult(
                success=True,
                data={
                    "prediction": {
                        "confidence": "low",
                        "message": "Insufficient historical data for prediction",
                    }
                },
            )

        # Calculate predictions
        predicted_duration = mean([m.execution_time for m in similar_executions])
        predicted_success_rate = mean([m.success_rate for m in similar_executions])
        confidence = min(
            len(similar_executions) / 10.0, 1.0
        )  # Max confidence at 10+ executions

        # Identify likely issues
        common_failures = self._analyze_failure_points(similar_executions)

        prediction = {
            "predicted_duration_seconds": predicted_duration,
            "predicted_success_rate": predicted_success_rate,
            "confidence_score": confidence,
            "potential_issues": common_failures.get("most_common", []),
            "based_on_executions": len(similar_executions),
            "recommendation": self._generate_execution_recommendation(
                predicted_success_rate, predicted_duration
            ),
        }

        return PluginResult(success=True, data={"prediction": prediction})

    async def _identify_patterns(self, params: Dict[str, Any]) -> PluginResult:
        """Identify execution patterns in workflow history."""
        min_frequency = params.get("min_frequency", 3)

        patterns = []

        # Pattern 1: Time-based performance variations
        time_patterns = self._analyze_time_patterns()
        patterns.extend(time_patterns)

        # Pattern 2: Step sequence patterns
        sequence_patterns = self._analyze_sequence_patterns()
        patterns.extend(sequence_patterns)

        # Pattern 3: Resource usage patterns
        resource_patterns = self._analyze_resource_patterns()
        patterns.extend(resource_patterns)

        # Filter by frequency
        significant_patterns = [p for p in patterns if p.frequency >= min_frequency]

        return PluginResult(
            success=True,
            data={
                "patterns": [asdict(p) for p in significant_patterns],
                "total_patterns_found": len(patterns),
                "significant_patterns": len(significant_patterns),
                "min_frequency_threshold": min_frequency,
            },
        )

    async def _recommend_optimizations(self, params: Dict[str, Any]) -> PluginResult:
        """Recommend workflow optimizations based on analysis."""
        workflow_definition = params.get("workflow_definition", {})
        performance_target = params.get(
            "performance_target", "balanced"
        )  # speed, reliability, cost

        recommendations = []

        # Analyze current workflow
        complexity = self._calculate_complexity(workflow_definition)
        risk_factors = self._identify_risk_factors(workflow_definition)

        # Generate recommendations based on target
        if performance_target == "speed":
            recommendations.extend(self._speed_optimizations(workflow_definition))
        elif performance_target == "reliability":
            recommendations.extend(self._reliability_optimizations(workflow_definition))
        elif performance_target == "cost":
            recommendations.extend(self._cost_optimizations(workflow_definition))
        else:  # balanced
            recommendations.extend(self._balanced_optimizations(workflow_definition))

        # Add pattern-based recommendations
        pattern_recommendations = [
            {
                "type": "pattern_based",
                "description": p.recommendation,
                "impact_score": p.impact_score,
                "evidence": f"Pattern observed {p.frequency} times",
            }
            for p in self.optimization_patterns
        ]
        recommendations.extend(pattern_recommendations)

        # Sort by impact score
        recommendations.sort(key=lambda x: x.get("impact_score", 0), reverse=True)

        return PluginResult(
            success=True,
            data={
                "recommendations": recommendations[:10],  # Top 10
                "performance_target": performance_target,
                "workflow_complexity": complexity,
                "total_recommendations": len(recommendations),
            },
        )

    async def _benchmark_workflow(self, params: Dict[str, Any]) -> PluginResult:
        """Benchmark workflow against similar workflows."""
        workflow_definition = params.get("workflow_definition", {})
        workflow_name = workflow_definition.get("name", "unknown")

        # Find similar workflows for comparison
        step_count = len(workflow_definition.get("steps", []))
        similar_workflows = {}

        for execution in self.execution_history:
            if (
                execution.step_count == step_count
                and execution.workflow_name != workflow_name
            ):
                if execution.workflow_name not in similar_workflows:
                    similar_workflows[execution.workflow_name] = []
                similar_workflows[execution.workflow_name].append(execution)

        # Calculate benchmarks
        benchmarks = {}
        for name, executions in similar_workflows.items():
            if len(executions) >= 3:  # Minimum for meaningful comparison
                benchmarks[name] = {
                    "average_duration": mean([e.execution_time for e in executions]),
                    "success_rate": mean([e.success_rate for e in executions]),
                    "executions": len(executions),
                }

        # Get current workflow performance
        current_performance = self._get_historical_performance(workflow_name)

        benchmark_result = {
            "current_workflow": {
                "name": workflow_name,
                "performance": current_performance,
            },
            "similar_workflows": benchmarks,
            "comparison_basis": f"workflows with {step_count} steps",
            "recommendations": self._generate_benchmark_recommendations(
                current_performance, benchmarks
            ),
        }

        return PluginResult(success=True, data={"benchmark": benchmark_result})

    def _calculate_complexity(self, workflow_definition: Dict[str, Any]) -> float:
        """Calculate workflow complexity score."""
        steps = workflow_definition.get("steps", [])
        complexity = len(steps)

        # Add complexity for conditional logic, loops, etc.
        for step in steps:
            if step.get("retry"):
                complexity += 0.5
            if step.get("conditions"):
                complexity += 1.0
            if step.get("parallel"):
                complexity += 1.5

        return complexity

    def _estimate_duration(self, workflow_definition: Dict[str, Any]) -> float:
        """Estimate workflow duration based on steps."""
        steps = workflow_definition.get("steps", [])
        # Simple estimation: 30 seconds per step average
        base_duration = len(steps) * 30.0

        # Adjust for known plugin types
        for step in steps:
            plugin_name = step.get("plugin_name", "")
            if "web_search" in plugin_name:
                base_duration += 10.0  # Web searches take longer
            elif "arango_db" in plugin_name:
                base_duration += 2.0  # DB operations are fast

        return base_duration

    def _identify_risk_factors(self, workflow_definition: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors in workflow."""
        risks = []
        steps = workflow_definition.get("steps", [])

        for i, step in enumerate(steps):
            plugin_name = step.get("plugin_name", "")

            # External dependency risks
            if "web_search" in plugin_name or "http" in plugin_name:
                risks.append(f"Step {i+1}: External dependency ({plugin_name})")

            # No retry configuration
            if not step.get("retry"):
                risks.append(f"Step {i+1}: No retry configuration")

            # Complex parameter mapping
            if len(step.get("inputs", {})) > 5:
                risks.append(f"Step {i+1}: Complex parameter mapping")

        return risks

    def _get_historical_performance(self, workflow_name: str) -> Dict[str, Any]:
        """Get historical performance for a workflow."""
        executions = [
            m for m in self.execution_history if m.workflow_name == workflow_name
        ]

        if not executions:
            return {"message": "No historical data available"}

        return {
            "executions": len(executions),
            "average_duration": mean([e.execution_time for e in executions]),
            "success_rate": mean([e.success_rate for e in executions]),
            "last_execution": max([e.timestamp for e in executions]).isoformat(),
        }

    def _identify_optimization_opportunities(
        self, workflow_definition: Dict[str, Any]
    ) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        steps = workflow_definition.get("steps", [])

        # Check for parallelization opportunities
        sequential_steps = [s for s in steps if not s.get("parallel")]
        if len(sequential_steps) > 2:
            opportunities.append("Consider parallelizing independent steps")

        # Check for caching opportunities
        db_steps = [s for s in steps if "arango_db" in s.get("plugin_name", "")]
        if len(db_steps) > 1:
            opportunities.append("Consider caching database query results")

        # Check for error handling
        steps_without_retry = [s for s in steps if not s.get("retry")]
        if len(steps_without_retry) > len(steps) * 0.5:
            opportunities.append("Add retry configuration to improve reliability")

        return opportunities

    def _estimate_success_probability(
        self, workflow_definition: Dict[str, Any]
    ) -> float:
        """Estimate workflow success probability."""
        base_probability = 0.95  # Start optimistic
        steps = workflow_definition.get("steps", [])

        # Reduce probability based on risk factors
        risk_factors = self._identify_risk_factors(workflow_definition)
        probability_reduction = len(risk_factors) * 0.05

        # Adjust for step count (more steps = more potential failures)
        step_reduction = len(steps) * 0.02

        final_probability = max(
            base_probability - probability_reduction - step_reduction, 0.1
        )
        return final_probability

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        characteristics = analysis.get("workflow_characteristics", {})
        complexity = characteristics.get("complexity_score", 0)
        risk_factors = characteristics.get("risk_factors", [])

        if complexity > 10:
            recommendations.append(
                "Consider breaking down complex workflow into smaller workflows"
            )

        if len(risk_factors) > 3:
            recommendations.append(
                "Address identified risk factors to improve reliability"
            )

        opportunities = analysis.get("optimization_opportunities", [])
        recommendations.extend(opportunities[:3])  # Top 3 opportunities

        return recommendations

    def _analyze_trends(self, executions: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze performance trends."""
        if len(executions) < 5:
            return {"message": "Insufficient data for trend analysis"}

        # Sort by timestamp
        sorted_executions = sorted(executions, key=lambda x: x.timestamp)

        # Calculate trends
        recent_half = sorted_executions[len(sorted_executions) // 2 :]
        older_half = sorted_executions[: len(sorted_executions) // 2]

        recent_avg_time = mean([e.execution_time for e in recent_half])
        older_avg_time = mean([e.execution_time for e in older_half])

        recent_success_rate = mean([e.success_rate for e in recent_half])
        older_success_rate = mean([e.success_rate for e in older_half])

        return {
            "performance_trend": (
                "improving" if recent_avg_time < older_avg_time else "declining"
            ),
            "reliability_trend": (
                "improving" if recent_success_rate > older_success_rate else "declining"
            ),
            "recent_avg_duration": recent_avg_time,
            "historical_avg_duration": older_avg_time,
            "recent_success_rate": recent_success_rate,
            "historical_success_rate": older_success_rate,
        }

    def _analyze_failure_points(
        self, executions: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Analyze common failure points."""
        all_failures = []
        for execution in executions:
            all_failures.extend(execution.failure_points)

        if not all_failures:
            return {"message": "No failures recorded"}

        # Count frequency of each failure point
        failure_counts = {}
        for failure in all_failures:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1

        # Sort by frequency
        sorted_failures = sorted(
            failure_counts.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "most_common": [f[0] for f in sorted_failures[:5]],
            "failure_frequency": dict(sorted_failures),
            "total_failures": len(all_failures),
        }

    def _analyze_resource_usage(
        self, executions: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Analyze resource usage patterns."""
        if not executions:
            return {"message": "No resource data available"}

        # This is a simplified analysis - would need more detailed resource tracking
        avg_execution_time = mean([e.execution_time for e in executions])

        return {
            "average_execution_time": avg_execution_time,
            "resource_efficiency": (
                "high"
                if avg_execution_time < 60
                else "medium"
                if avg_execution_time < 300
                else "low"
            ),
        }

    def _analyze_time_patterns(self) -> List[OptimizationPattern]:
        """Analyze time-based execution patterns."""
        patterns = []

        # Group executions by hour of day
        hour_performance = {}
        for execution in self.execution_history:
            hour = execution.timestamp.hour
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(execution.execution_time)

        # Find patterns
        for hour, times in hour_performance.items():
            if len(times) >= 3:
                avg_time = mean(times)
                if avg_time < 30:  # Fast execution times
                    patterns.append(
                        OptimizationPattern(
                            pattern_type="time_based",
                            description=f"Faster execution during hour {hour}",
                            impact_score=0.3,
                            frequency=len(times),
                            recommendation=f"Schedule workflows around hour {hour} for better performance",
                        )
                    )

        return patterns

    def _analyze_sequence_patterns(self) -> List[OptimizationPattern]:
        """Analyze step sequence patterns."""
        # This would analyze common step sequences and their success rates
        # Simplified implementation for now
        return []

    def _analyze_resource_patterns(self) -> List[OptimizationPattern]:
        """Analyze resource usage patterns."""
        # This would analyze resource usage patterns
        # Simplified implementation for now
        return []

    def _speed_optimizations(
        self, workflow_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate speed-focused optimizations."""
        return [
            {
                "type": "speed",
                "description": "Enable parallel execution for independent steps",
                "impact_score": 0.8,
                "implementation": "Add 'parallel': true to independent steps",
            },
            {
                "type": "speed",
                "description": "Optimize database queries",
                "impact_score": 0.6,
                "implementation": "Use batch operations and indexing",
            },
        ]

    def _reliability_optimizations(
        self, workflow_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate reliability-focused optimizations."""
        return [
            {
                "type": "reliability",
                "description": "Add retry configuration to all external dependencies",
                "impact_score": 0.9,
                "implementation": "Configure retry with exponential backoff",
            },
            {
                "type": "reliability",
                "description": "Implement circuit breaker pattern",
                "impact_score": 0.7,
                "implementation": "Add failure thresholds and fallback mechanisms",
            },
        ]

    def _cost_optimizations(
        self, workflow_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate cost-focused optimizations."""
        return [
            {
                "type": "cost",
                "description": "Use more efficient AI models for simple tasks",
                "impact_score": 0.8,
                "implementation": "Switch to gpt-4.1-nano for basic operations",
            },
            {
                "type": "cost",
                "description": "Implement result caching",
                "impact_score": 0.6,
                "implementation": "Cache expensive operation results",
            },
        ]

    def _balanced_optimizations(
        self, workflow_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate balanced optimizations."""
        optimizations = []
        optimizations.extend(self._speed_optimizations(workflow_definition)[:1])
        optimizations.extend(self._reliability_optimizations(workflow_definition)[:1])
        optimizations.extend(self._cost_optimizations(workflow_definition)[:1])
        return optimizations

    def _generate_execution_recommendation(
        self, success_rate: float, duration: float
    ) -> str:
        """Generate execution recommendation based on predictions."""
        if success_rate > 0.9 and duration < 120:
            return "Excellent performance expected - proceed with confidence"
        elif success_rate > 0.7:
            return "Good performance expected - monitor for issues"
        else:
            return "Consider workflow optimization before execution"

    def _generate_benchmark_recommendations(
        self, current: Dict[str, Any], benchmarks: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on benchmark comparison."""
        recommendations = []

        if not benchmarks:
            recommendations.append("No similar workflows found for comparison")
            return recommendations

        # Compare performance
        current_duration = current.get("average_duration", float("inf"))
        benchmark_durations = [b["average_duration"] for b in benchmarks.values()]

        if benchmark_durations and current_duration > mean(benchmark_durations):
            recommendations.append("Performance below average - consider optimization")

        current_success = current.get("success_rate", 0)
        benchmark_success = [b["success_rate"] for b in benchmarks.values()]

        if benchmark_success and current_success < mean(benchmark_success):
            recommendations.append("Reliability below average - improve error handling")

        return recommendations

    async def _update_patterns(self):
        """Update optimization patterns based on recent data."""
        # This would implement pattern learning algorithms
        # Simplified for now - just analyze time patterns
        new_patterns = self._analyze_time_patterns()

        # Merge with existing patterns
        for new_pattern in new_patterns:
            existing = next(
                (
                    p
                    for p in self.optimization_patterns
                    if p.description == new_pattern.description
                ),
                None,
            )
            if existing:
                existing.frequency += new_pattern.frequency
            else:
                self.optimization_patterns.append(new_pattern)

    def _load_historical_data(self, historical_data: Dict[str, Any]):
        """Load historical execution data."""
        # This would load data from persistent storage
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="analyze",
                description="Analyze workflow performance and characteristics",
            ),
            Capability(
                name="record_execution",
                description="Record workflow execution for learning",
            ),
            Capability(
                name="get_insights",
                description="Get workflow execution insights and trends",
            ),
            Capability(
                name="predict_performance",
                description="Predict workflow performance based on history",
            ),
            Capability(
                name="identify_patterns",
                description="Identify execution patterns in workflow history",
            ),
            Capability(
                name="recommend_optimizations",
                description="Recommend workflow optimizations",
            ),
            Capability(
                name="benchmark_workflow",
                description="Benchmark workflow against similar workflows",
            ),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data."""
        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def get_dependencies() -> List[str]:
        """External dependencies."""
        return []

    @staticmethod
    def get_configuration_schema() -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "learning_enabled": {"type": "boolean"},
                "historical_data": {"type": "object"},
            },
        }
