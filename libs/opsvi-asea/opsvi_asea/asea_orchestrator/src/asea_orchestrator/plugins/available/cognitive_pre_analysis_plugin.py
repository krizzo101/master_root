"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See cognitive_pre_analysis_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)

from typing import List, Any, Optional, Dict
import os
import json
from datetime import datetime
from openai import AsyncOpenAI
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class CognitivePreAnalysisPlugin(BasePlugin):
    """
    Pre-analyzes user prompts to enhance agent understanding before main response.
    Identifies key challenges, research needs, potential pitfalls, and optimal thinking approaches.
    """

    def __init__(self):
        super().__init__()
        self.client: Optional[AsyncOpenAI] = None
        self.analysis_model = "gpt-4.1-mini"

    @staticmethod
    def get_name() -> str:
        return "cognitive_pre_analysis"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize OpenAI client for pre-analysis."""
        self.event_bus = event_bus

        api_key = config.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided in config or environment")

        self.client = AsyncOpenAI(api_key=api_key)
        self.analysis_model = config.config.get("analysis_model", "gpt-4.1-mini")

        print(f"Cognitive Pre-Analysis initialized with model: {self.analysis_model}")

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute pre-analysis of user prompt."""
        try:
            params = context.state
            user_prompt = params.get("user_prompt")
            context_data = params.get("context", {})
            analysis_depth = params.get(
                "analysis_depth", "standard"
            )  # quick, standard, deep

            if not user_prompt:
                return PluginResult(
                    success=False,
                    error_message="user_prompt is required for pre-analysis",
                )

            # Perform pre-analysis
            analysis = await self._analyze_prompt(
                user_prompt, context_data, analysis_depth
            )

            return PluginResult(
                success=True,
                data={
                    "pre_analysis": analysis,
                    "enhanced_understanding": analysis.get(
                        "enhanced_understanding", ""
                    ),
                    "research_priorities": analysis.get("research_priorities", []),
                    "thinking_approach": analysis.get("thinking_approach", ""),
                    "potential_challenges": analysis.get("potential_challenges", []),
                    "success_factors": analysis.get("success_factors", []),
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Pre-analysis error: {str(e)}"
            )

    async def _analyze_prompt(
        self, user_prompt: str, context: Dict[str, Any], depth: str
    ) -> Dict[str, Any]:
        """Analyze user prompt to enhance understanding."""

        analysis_prompt = f"""
        COGNITIVE PRE-ANALYSIS TASK

        User Prompt: {user_prompt}
        
        Context: {json.dumps(context, indent=2) if context else "No additional context"}
        
        Analysis Depth: {depth}

        Perform cognitive pre-analysis to help an AI agent better understand and respond to this prompt.

        Analyze:
        1. **Core Intent**: What is the user really asking for?
        2. **Key Challenges**: What makes this request complex or difficult?
        3. **Research Priorities**: What information should be gathered first?
        4. **Thinking Approach**: What cognitive strategies would be most effective?
        5. **Potential Pitfalls**: What could go wrong or be misunderstood?
        6. **Success Factors**: What would make the response excellent?
        7. **Enhanced Understanding**: Reframe the request with deeper insight

        Respond with JSON:
        {{
            "core_intent": "what user really wants",
            "complexity_level": "simple|moderate|complex|expert",
            "key_challenges": ["challenge1", "challenge2"],
            "research_priorities": ["priority1", "priority2"],
            "thinking_approach": "recommended cognitive strategy",
            "potential_pitfalls": ["pitfall1", "pitfall2"],
            "success_factors": ["factor1", "factor2"],
            "enhanced_understanding": "deeper insight into the request",
            "recommended_tools": ["tool1", "tool2"],
            "estimated_complexity": "1-10 scale"
        }}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cognitive analysis specialist who helps AI agents better understand user requests. Provide structured analysis that enhances comprehension and response quality.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                max_tokens=1000,
                temperature=0.1,
            )

            analysis_result = response.choices[0].message.content
            usage = response.usage

            # Parse JSON response
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis_data = {
                    "enhanced_understanding": analysis_result,
                    "core_intent": "Analysis parsing failed - raw response provided",
                    "complexity_level": "unknown",
                }

            # Add metadata
            analysis_data["analysis_metadata"] = {
                "model_used": self.analysis_model,
                "tokens_used": {
                    "input": usage.prompt_tokens,
                    "output": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": depth,
            }

            return analysis_data

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "enhanced_understanding": f"Pre-analysis failed, proceeding with original prompt: {user_prompt}",
                "core_intent": "unknown due to analysis failure",
            }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="analyze_prompt",
                description="Pre-analyze user prompts to enhance agent understanding",
            )
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data."""
        if not isinstance(input_data, dict):
            return ValidationResult(
                is_valid=False, errors=["Input must be a dictionary"]
            )

        if "user_prompt" not in input_data:
            return ValidationResult(is_valid=False, errors=["user_prompt is required"])

        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def get_dependencies() -> List[str]:
        """External dependencies."""
        return ["openai"]

    @staticmethod
    def get_configuration_schema() -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "openai_api_key": {"type": "string"},
                "analysis_model": {"type": "string", "default": "gpt-4.1-mini"},
            },
            "required": ["openai_api_key"],
        }
