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


class CognitiveCriticPlugin(BasePlugin):
    """
    Reviews and critiques agent responses before finalization.
    Identifies logical gaps, weak reasoning, missing perspectives, and improvement opportunities.
    """

    def __init__(self):
        super().__init__()
        self.client: Optional[AsyncOpenAI] = None
        self.critic_model = "gpt-4.1"

    @staticmethod
    def get_name() -> str:
        return "cognitive_critic"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize OpenAI client for critique."""
        self.event_bus = event_bus

        api_key = config.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided in config or environment")

        self.client = AsyncOpenAI(api_key=api_key)
        self.critic_model = config.config.get("critic_model", "gpt-4.1")

        print(f"Cognitive Critic initialized with model: {self.critic_model}")

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute critique of response."""
        try:
            params = context.state
            original_prompt = params.get("original_prompt")
            agent_response = params.get("agent_response")
            critique_focus = params.get(
                "critique_focus", "comprehensive"
            )  # logic, completeness, accuracy, comprehensive

            if not agent_response:
                return PluginResult(
                    success=False,
                    error_message="agent_response is required for critique",
                )

            # Perform critique
            critique = await self._critique_response(
                original_prompt, agent_response, critique_focus
            )

            return PluginResult(
                success=True,
                data={
                    "critique": critique,
                    "needs_revision": critique.get("needs_revision", False),
                    "revision_priority": critique.get("revision_priority", "low"),
                    "specific_issues": critique.get("specific_issues", []),
                    "improvement_suggestions": critique.get(
                        "improvement_suggestions", []
                    ),
                    "quality_score": critique.get("quality_score", 0),
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Critique error: {str(e)}"
            )

    async def _critique_response(
        self, original_prompt: str, response: str, focus: str
    ) -> Dict[str, Any]:
        """Critique agent response for quality and completeness."""

        critique_prompt = f"""
        COGNITIVE CRITIQUE TASK

        Original User Prompt: {original_prompt or "Not provided"}
        
        Agent Response to Critique:
        {response}
        
        Critique Focus: {focus}

        As an expert critic, thoroughly analyze this response for quality, accuracy, and completeness.

        Evaluate:
        1. **Logical Consistency**: Are the arguments logical and well-reasoned?
        2. **Completeness**: Does it fully address the user's request?
        3. **Accuracy**: Are the facts and claims accurate?
        4. **Clarity**: Is the response clear and well-structured?
        5. **Missing Elements**: What important aspects are missing?
        6. **Assumptions**: What assumptions were made that should be questioned?
        7. **Alternative Perspectives**: What other viewpoints should be considered?

        Provide constructive critique with specific improvement suggestions.

        Respond with JSON:
        {{
            "quality_score": 1-10,
            "needs_revision": true/false,
            "revision_priority": "low|medium|high|critical",
            "strengths": ["strength1", "strength2"],
            "specific_issues": [
                {{"issue": "description", "severity": "low|medium|high", "suggestion": "how to fix"}}
            ],
            "missing_elements": ["element1", "element2"],
            "logical_gaps": ["gap1", "gap2"],
            "accuracy_concerns": ["concern1", "concern2"],
            "improvement_suggestions": ["suggestion1", "suggestion2"],
            "alternative_approaches": ["approach1", "approach2"],
            "overall_assessment": "detailed critique summary"
        }}
        """

        try:
            response_obj = await self.client.chat.completions.create(
                model=self.critic_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert critic who provides constructive, detailed feedback on AI responses. Your goal is to improve response quality through specific, actionable critique.",
                    },
                    {"role": "user", "content": critique_prompt},
                ],
                max_tokens=1500,
                temperature=0.1,
            )

            critique_result = response_obj.choices[0].message.content
            usage = response_obj.usage

            # Parse JSON response
            try:
                critique_data = json.loads(critique_result)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                critique_data = {
                    "overall_assessment": critique_result,
                    "quality_score": 5,
                    "needs_revision": False,
                    "revision_priority": "low",
                }

            # Add metadata
            critique_data["critique_metadata"] = {
                "model_used": self.critic_model,
                "tokens_used": {
                    "input": usage.prompt_tokens,
                    "output": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
                "critique_timestamp": datetime.now().isoformat(),
                "critique_focus": focus,
            }

            return critique_data

        except Exception as e:
            return {
                "error": f"Critique failed: {str(e)}",
                "quality_score": 5,
                "needs_revision": False,
                "revision_priority": "low",
                "overall_assessment": f"Critique failed due to error: {str(e)}",
            }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="critique_response",
                description="Critique agent responses for quality and completeness",
            )
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data."""
        if not isinstance(input_data, dict):
            return ValidationResult(
                is_valid=False, errors=["Input must be a dictionary"]
            )

        if "agent_response" not in input_data:
            return ValidationResult(
                is_valid=False, errors=["agent_response is required"]
            )

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
                "critic_model": {"type": "string", "default": "gpt-4.1"},
            },
            "required": ["openai_api_key"],
        }
