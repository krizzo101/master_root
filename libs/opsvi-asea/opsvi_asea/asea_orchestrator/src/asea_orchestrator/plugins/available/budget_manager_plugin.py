"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See budget_manager_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)

from typing import List, Any, Optional, Dict
from datetime import datetime, date
from dataclasses import dataclass, asdict
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


@dataclass
class BudgetLimit:
    """Budget limit configuration"""

    daily_limit_usd: float
    weekly_limit_usd: float
    monthly_limit_usd: float
    model_preferences: Dict[str, str]  # task_type -> preferred_model


@dataclass
class TokenUsage:
    """Token usage tracking"""

    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime


class BudgetManagerPlugin(BasePlugin):
    """
    Manages AI model budgets and token usage tracking.
    Provides cost estimation and budget enforcement.
    """

    def __init__(self):
        super().__init__()
        self.budget_limits: Optional[BudgetLimit] = None
        self.current_usage: Dict[str, float] = {}  # date -> cost_usd

        # Current OpenAI pricing (per 1M tokens) - Updated with latest models
        self.model_pricing = {
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o4-mini": {"input": 1.10, "output": 4.40},
            "o3": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 3.00, "output": 12.00},
            # Legacy models (deprecated)
            # "gpt-4o": {"input": 2.50, "output": 10.00},
            # "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-opus": {"input": 15.00, "output": 75.00},
        }

        # Model categories for optimization recommendations
        self.thinking_models = {"o3", "o4-mini", "o3-mini"}
        self.efficient_models = {"gpt-4.1-mini", "gpt-4.1-nano"}
        self.premium_models = {"gpt-4.1", "o3"}

    @staticmethod
    def get_name() -> str:
        return "budget_manager"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize budget manager with configuration."""
        # Call parent initialize to set up AI capabilities
        await super().initialize(config, event_bus)

        # Load budget configuration
        budget_config = config.config.get("budget_limits", {})
        self.budget_limits = BudgetLimit(
            daily_limit_usd=budget_config.get("daily_limit_usd", 10.0),
            weekly_limit_usd=budget_config.get("weekly_limit_usd", 50.0),
            monthly_limit_usd=budget_config.get("monthly_limit_usd", 200.0),
            model_preferences=budget_config.get(
                "model_preferences",
                {
                    "reasoning": "o4-mini",
                    "simple": "gpt-4.1-nano",
                    "complex": "gpt-4.1",
                    "default": "gpt-4.1-mini",
                },
            ),
        )

        print(
            f"Budget Manager initialized with daily limit: ${self.budget_limits.daily_limit_usd}"
        )

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute budget management operations."""
        try:
            params = context.state
            # Handle both 'action' and 'operation' parameters for backward compatibility
            action = params.get("action") or params.get("operation", "check_budget")

            # Handle specific operations used by cognitive enhancement
            if action == "analyze_decision_costs":
                return await self._analyze_decision_costs(params)
            elif action == "check_budget":
                return await self._check_budget(params)
            elif action == "estimate_cost":
                return await self._estimate_cost(params)
            elif action == "record_usage":
                return await self._record_usage(params)
            elif action == "get_recommended_model":
                return await self._get_recommended_model(params)
            elif action == "get_usage_stats":
                return await self._get_usage_stats(params)
            else:
                return PluginResult(
                    success=False, error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Budget manager error: {str(e)}"
            )

    async def _analyze_decision_costs(self, params: Dict[str, Any]) -> PluginResult:
        """Analyze costs and budget implications for decision making using AI."""
        context = params.get("context", {})

        # Extract decision analysis parameters
        decision_options = context.get("decision_options", [])
        estimated_cost = context.get("estimated_cost_usd", 0.0)
        priority = context.get("priority", "medium")

        # Perform basic budget check
        budget_check = await self._check_budget(
            {"estimated_cost_usd": estimated_cost, "period": "daily"}
        )

        # Use AI to analyze decision costs and generate recommendations
        analysis_prompt = f"""
Analyze the budget implications for this decision:

Decision Options: {decision_options}
Estimated Cost: ${estimated_cost}
Priority: {priority}
Budget Status: {budget_check.data}

Provide:
1. Analysis of each decision option's cost implications
2. Budget viability assessment
3. Specific recommendations for cost optimization
4. Risk assessment for budget constraints
"""

        # Use shared AI capabilities for structured analysis
        ai_response = await self.create_structured_ai_response(
            operation="analyze_decision_costs",
            prompt=analysis_prompt,
            context={
                "option_count": len(decision_options),
                "budget_constrained": not budget_check.data["can_proceed"],
                "priority_level": priority,
            },
            max_tokens=1500,
        )

        if ai_response["success"]:
            # Use AI-generated analysis
            ai_data = ai_response["data"]
            return PluginResult(
                success=True,
                data={
                    **ai_data,
                    "budget_status": budget_check.data,
                    "ai_enhanced": True,
                    "model_used": ai_response.get("model"),
                    "cost_info": ai_response.get("cost_info"),
                },
            )
        else:
            # Fallback to basic analysis if AI fails
            return await self._basic_cost_analysis(
                budget_check, decision_options, estimated_cost, priority
            )

    async def _basic_cost_analysis(
        self, budget_check, decision_options, estimated_cost, priority
    ):
        """Fallback basic cost analysis without AI."""
        recommendations = []
        cost_analysis = {
            "budget_status": budget_check.data,
            "decision_cost_analysis": {},
            "recommendations": recommendations,
            "ai_enhanced": False,
        }

        if budget_check.data["can_proceed"]:
            recommendations.append(
                "Budget allows for this decision - proceed with implementation"
            )
            cost_analysis["decision_viability"] = "approved"
        else:
            recommendations.append(
                "Decision exceeds budget limits - consider cost optimization"
            )
            cost_analysis["decision_viability"] = "budget_constrained"

        # Basic option analysis
        if decision_options:
            option_analysis = {}
            for i, option in enumerate(decision_options):
                if isinstance(option, str):
                    option_cost = estimated_cost * (
                        1.5
                        if "expensive" in option.lower()
                        else 0.5
                        if "cheap" in option.lower()
                        else 1.0
                    )
                    option_analysis[f"option_{i+1}"] = {
                        "description": option,
                        "estimated_cost": option_cost,
                        "budget_impact": "high"
                        if option_cost > budget_check.data["remaining_budget"] * 0.5
                        else "low",
                        "recommendation": "Consider carefully"
                        if option_cost > budget_check.data["remaining_budget"] * 0.5
                        else "Proceed",
                    }
            cost_analysis["decision_cost_analysis"] = option_analysis

        return PluginResult(success=True, data=cost_analysis)

    async def _check_budget(self, params: Dict[str, Any]) -> PluginResult:
        """Check if budget allows for operation."""
        estimated_cost = params.get("estimated_cost_usd", 0.0)
        period = params.get("period", "daily")  # daily, weekly, monthly

        today = date.today().isoformat()
        current_usage = self.current_usage.get(today, 0.0)

        if period == "daily":
            limit = self.budget_limits.daily_limit_usd
            remaining = limit - current_usage
        elif period == "weekly":
            # Simplified - would need proper week calculation
            limit = self.budget_limits.weekly_limit_usd
            remaining = limit - current_usage
        else:  # monthly
            limit = self.budget_limits.monthly_limit_usd
            remaining = limit - current_usage

        can_proceed = estimated_cost <= remaining

        return PluginResult(
            success=True,
            data={
                "can_proceed": can_proceed,
                "remaining_budget": remaining,
                "estimated_cost": estimated_cost,
                "current_usage": current_usage,
                "limit": limit,
                "utilization_percent": (
                    (current_usage / limit) * 100 if limit > 0 else 0
                ),
            },
        )

    async def _estimate_cost(self, params: Dict[str, Any]) -> PluginResult:
        """Estimate cost for AI operation."""
        model = params.get("model", "gpt-4.1-mini")
        input_tokens = params.get("input_tokens", 0)
        estimated_output_tokens = params.get("estimated_output_tokens", 0)

        if model not in self.model_pricing:
            return PluginResult(success=False, error_message=f"Unknown model: {model}")

        pricing = self.model_pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return PluginResult(
            success=True,
            data={
                "model": model,
                "input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "input_cost_usd": input_cost,
                "output_cost_usd": output_cost,
                "total_estimated_cost_usd": total_cost,
                "cost_per_1k_tokens": {
                    "input": pricing["input"] / 1000,
                    "output": pricing["output"] / 1000,
                },
            },
        )

    async def _record_usage(self, params: Dict[str, Any]) -> PluginResult:
        """Record actual usage after AI operation."""
        model = params.get("model")
        input_tokens = params.get("input_tokens", 0)
        output_tokens = params.get("output_tokens", 0)

        if not model or model not in self.model_pricing:
            return PluginResult(
                success=False,
                error_message=f"Invalid model for usage recording: {model}",
            )

        pricing = self.model_pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        # Update current usage
        today = date.today().isoformat()
        self.current_usage[today] = self.current_usage.get(today, 0.0) + total_cost

        usage_record = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
            timestamp=datetime.now(),
        )

        return PluginResult(
            success=True,
            data={
                "usage_record": asdict(usage_record),
                "daily_total_cost": self.current_usage[today],
                "remaining_daily_budget": self.budget_limits.daily_limit_usd
                - self.current_usage[today],
            },
        )

    async def _get_recommended_model(self, params: Dict[str, Any]) -> PluginResult:
        """Get recommended model based on task type and budget."""
        task_type = params.get("task_type", "default")
        max_cost = params.get("max_cost_usd", None)

        preferred_model = self.budget_limits.model_preferences.get(
            task_type, self.budget_limits.model_preferences["default"]
        )

        # If max_cost specified, ensure model fits budget with realistic token estimates
        if max_cost:
            # Estimate cost for typical operation (500 input + 1000 output tokens)
            pricing = self.model_pricing[preferred_model]
            estimated_cost = (500 / 1_000_000) * pricing["input"] + (
                1000 / 1_000_000
            ) * pricing["output"]
            if estimated_cost > max_cost:
                # Find most capable model within budget
                affordable_models = []
                for model, pricing in self.model_pricing.items():
                    model_cost = (500 / 1_000_000) * pricing["input"] + (
                        1000 / 1_000_000
                    ) * pricing["output"]
                    if model_cost <= max_cost:
                        affordable_models.append((model, model_cost))

                if affordable_models:
                    # Sort by cost (ascending) and pick the most expensive within budget
                    affordable_models.sort(key=lambda x: x[1], reverse=True)
                    preferred_model = affordable_models[0][0]
                else:
                    preferred_model = "gpt-4.1-nano"  # Ultimate fallback

        return PluginResult(
            success=True,
            data={
                "recommended_model": preferred_model,
                "task_type": task_type,
                "reasoning": f"Selected {preferred_model} for {task_type} task type",
                "cost_per_1k_input_tokens": self.model_pricing[preferred_model]["input"]
                / 1000,
                "cost_per_1k_output_tokens": self.model_pricing[preferred_model][
                    "output"
                ]
                / 1000,
            },
        )

    async def _get_usage_stats(self, params: Dict[str, Any]) -> PluginResult:
        """Get usage statistics."""
        today = date.today().isoformat()
        current_usage = self.current_usage.get(today, 0.0)

        return PluginResult(
            success=True,
            data={
                "current_daily_usage": current_usage,
                "daily_limit": self.budget_limits.daily_limit_usd,
                "remaining_daily_budget": self.budget_limits.daily_limit_usd
                - current_usage,
                "utilization_percent": (
                    current_usage / self.budget_limits.daily_limit_usd
                )
                * 100,
                "model_preferences": self.budget_limits.model_preferences,
                "available_models": list(self.model_pricing.keys()),
            },
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="check_budget",
                description="Check if budget allows for AI operation",
            ),
            Capability(
                name="estimate_cost",
                description="Estimate cost for AI operation before execution",
            ),
            Capability(
                name="record_usage",
                description="Record actual token usage and cost after AI operation",
            ),
            Capability(
                name="get_recommended_model",
                description="Get recommended AI model based on task type and budget",
            ),
            Capability(
                name="get_usage_stats",
                description="Get current usage statistics and budget status",
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
                "budget_limits": {
                    "type": "object",
                    "properties": {
                        "daily_limit_usd": {"type": "number", "minimum": 0},
                        "weekly_limit_usd": {"type": "number", "minimum": 0},
                        "monthly_limit_usd": {"type": "number", "minimum": 0},
                        "model_preferences": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                }
            },
        }
