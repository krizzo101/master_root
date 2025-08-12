"""
AI Mixin for plugins to provide shared structured AI response capabilities.
Centralizes all AI API calls, cost tracking, and error handling in one place.
"""

from typing import Any, Dict, Optional, Type, TypeVar, List
import json
from pydantic import BaseModel
from ..responses_api_client_fixed import ResponsesAPIClientFixed

T = TypeVar("T", bound=BaseModel)


class AIMixin:
    """
    Mixin class that provides shared AI capabilities to all plugins.
    Handles structured responses, cost tracking, and error handling centrally.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ai_client: Optional[ResponsesAPIClientFixed] = None
        self._ai_config: Dict[str, Any] = {}

    def initialize_ai_client(
        self, api_key: str, ai_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize shared AI client for this plugin."""
        self._ai_client = ResponsesAPIClientFixed(api_key)
        self._ai_config = ai_config or {}

    async def create_structured_ai_response(
        self,
        operation: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
        custom_schema: Optional[Type[BaseModel]] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured AI response using the plugin's schema.

        Args:
            operation: The operation being performed (for schema lookup)
            prompt: The main prompt/question for the AI
            context: Additional context data
            model: Model to use (auto-selected if None)
            max_tokens: Maximum tokens to generate
            temperature: Temperature setting
            custom_schema: Custom Pydantic schema (overrides plugin schema)

        Returns:
            Dictionary with structured response data and metadata
        """
        if not self._ai_client:
            return {
                "success": False,
                "error": "AI client not initialized",
                "error_type": "configuration_error",
            }

        try:
            # Get plugin name for schema lookup
            plugin_name = self.get_name() if hasattr(self, "get_name") else "unknown"

            # Auto-select model if not specified
            if not model:
                model = "gpt-4.1-mini"  # Default to efficient model

            # Build comprehensive instructions
            instructions = self._build_ai_instructions(operation, plugin_name, context)

            # Create structured response
            if custom_schema:
                response_result = await self._ai_client.create_structured_response(
                    model=model,
                    instructions=instructions,
                    user_input=prompt,
                    response_schema=custom_schema,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response_result = await self._ai_client.create_response_for_plugin(
                    plugin_type=plugin_name,
                    operation=operation,
                    model=model,
                    instructions=instructions,
                    user_input=prompt,
                    use_structured=True,
                )

            # Add plugin-specific metadata
            response_result["plugin_name"] = plugin_name
            response_result["operation"] = operation
            response_result["auto_selected_model"] = model if not model else False

            return response_result

        except Exception as e:
            return {
                "success": False,
                "error": f"AI response creation failed: {str(e)}",
                "error_type": "execution_error",
                "plugin_name": getattr(self, "get_name", lambda: "unknown")(),
            }

    async def create_simple_ai_analysis(
        self,
        analysis_prompt: str,
        data_to_analyze: Any,
        analysis_type: str = "general",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a simple AI analysis without complex schemas.

        Args:
            analysis_prompt: What kind of analysis to perform
            data_to_analyze: The data to analyze
            analysis_type: Type of analysis (general, cost, performance, etc.)
            model: Model to use (auto-selected if None)

        Returns:
            Dictionary with analysis results
        """
        # Convert data to string if needed
        if isinstance(data_to_analyze, dict):
            data_str = json.dumps(data_to_analyze, indent=2)
        elif not isinstance(data_to_analyze, str):
            data_str = str(data_to_analyze)
        else:
            data_str = data_to_analyze

        full_prompt = f"""
{analysis_prompt}

Data to analyze:
{data_str}

Provide a clear, structured analysis focusing on actionable insights.
"""

        return await self.create_structured_ai_response(
            operation="analyze",
            prompt=full_prompt,
            context={"analysis_type": analysis_type},
            model=model,
            max_tokens=1500,
        )

    async def create_ai_recommendations(
        self,
        situation: str,
        available_options: List[str],
        constraints: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI recommendations for a given situation.

        Args:
            situation: Description of the current situation
            available_options: List of available options/actions
            constraints: List of constraints to consider
            model: Model to use

        Returns:
            Dictionary with recommendations
        """
        constraints_str = ""
        if constraints:
            constraints_str = "\nConstraints to consider:\n" + "\n".join(
                f"- {c}" for c in constraints
            )

        prompt = f"""
Situation: {situation}

Available options:
{chr(10).join(f"- {option}" for option in available_options)}
{constraints_str}

Provide specific recommendations with reasoning for each option.
"""

        return await self.create_structured_ai_response(
            operation="recommend",
            prompt=prompt,
            context={
                "option_count": len(available_options),
                "has_constraints": bool(constraints),
            },
            model=model,
            max_tokens=1800,
        )

    def _infer_task_type(self, operation: str, prompt: str) -> str:
        """Infer the type of task based on operation and prompt content."""
        operation_lower = operation.lower()
        prompt_lower = prompt.lower()

        if any(
            word in operation_lower
            for word in ["analyze", "analysis", "assess", "evaluate"]
        ):
            return "analysis"
        elif any(
            word in operation_lower for word in ["optimize", "improve", "enhance"]
        ):
            return "optimization"
        elif any(word in operation_lower for word in ["reason", "think", "decide"]):
            return "reasoning"
        elif any(
            word in operation_lower for word in ["recommend", "suggest", "advise"]
        ):
            return "creative"
        elif any(
            word in prompt_lower for word in ["complex", "difficult", "challenging"]
        ):
            return "complex_decision"
        elif any(word in prompt_lower for word in ["simple", "basic", "quick"]):
            return "simple_classification"
        else:
            return "reasoning"  # Default to reasoning for most plugin operations

    def _infer_complexity(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Infer complexity level based on prompt and context."""
        prompt_lower = prompt.lower()

        # Check context for complexity indicators
        if context:
            option_count = context.get("option_count", 0)
            constraint_count = context.get("constraint_count", 0)

            if option_count > 5 or constraint_count > 3:
                return "high"
            elif option_count > 2 or constraint_count > 1:
                return "medium"

        # Check prompt content
        complexity_indicators = {
            "high": [
                "complex",
                "comprehensive",
                "detailed",
                "thorough",
                "multi-step",
                "strategic",
            ],
            "low": ["simple", "basic", "quick", "brief", "straightforward"],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return level

        # Check prompt length as complexity indicator
        if len(prompt) > 500:
            return "high"
        elif len(prompt) > 200:
            return "medium"
        else:
            return "low"

    def _build_ai_instructions(
        self, operation: str, plugin_name: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive instructions for the AI based on plugin and operation."""
        base_instructions = f"""You are an expert assistant specialized in {plugin_name} operations.

Operation: {operation}
Plugin Context: {plugin_name}

Your expertise includes:
- Deep knowledge of {plugin_name} domain and best practices
- Ability to provide actionable, specific recommendations
- Understanding of operational constraints and real-world limitations
- Focus on practical, implementable solutions

Guidelines:
1. Provide specific, actionable insights
2. Consider real-world constraints and limitations
3. Structure your response clearly and logically
4. Include confidence levels where appropriate
5. Highlight key risks and mitigation strategies"""

        # Add context-specific instructions
        if context:
            context_info = json.dumps(context, indent=2)
            base_instructions += f"\n\nAdditional Context:\n{context_info}"

        # Add operation-specific guidance
        operation_guidance = {
            "analyze": "Focus on thorough analysis with supporting evidence and clear conclusions.",
            "optimize": "Provide specific optimization strategies with measurable impact estimates.",
            "recommend": "Give prioritized recommendations with clear reasoning and implementation steps.",
            "assess": "Provide comprehensive assessment with risk factors and success probability.",
            "plan": "Create detailed, step-by-step plans with timelines and resource requirements.",
        }

        if operation in operation_guidance:
            base_instructions += (
                f"\n\nOperation-Specific Guidance: {operation_guidance[operation]}"
            )

        return base_instructions

    async def cleanup_ai_client(self):
        """Cleanup AI client resources."""
        if self._ai_client:
            await self._ai_client.close()
            self._ai_client = None


class SharedAIManager:
    """
    Singleton manager for shared AI resources across all plugins.
    Ensures efficient resource usage and centralized configuration.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.api_key: Optional[str] = None
            self.ai_config: Dict[str, Any] = {}
            self.active_clients: List[ResponsesAPIClientFixed] = []
            self._initialized = True

    def initialize(self, api_key: str, ai_config: Optional[Dict[str, Any]] = None):
        """Initialize shared AI configuration."""
        self.api_key = api_key
        self.ai_config = ai_config or {}

    def get_ai_client(self) -> ResponsesAPIClientFixed:
        """Get a shared AI client instance."""
        if not self.api_key:
            raise ValueError("SharedAIManager not initialized with API key")

        client = ResponsesAPIClientFixed(self.api_key)
        self.active_clients.append(client)
        return client

    async def cleanup_all_clients(self):
        """Cleanup all active AI clients."""
        for client in self.active_clients:
            try:
                await client.close()
            except Exception:
                pass  # Ignore cleanup errors
        self.active_clients.clear()

    def get_config(self) -> Dict[str, Any]:
        """Get shared AI configuration."""
        return self.ai_config.copy()


# Global instance for easy access
shared_ai_manager = SharedAIManager()
