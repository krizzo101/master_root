from typing import List, Any, Optional, Dict
import os
import json
import asyncio
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
from asea_orchestrator.responses_api_client import ResponsesAPIClient
from asea_orchestrator.schemas import ReasoningAnalysis


class AIReasoningPlugin(BasePlugin):
    """
    Core AI reasoning plugin using OpenAI models for intelligent decision making.
    Provides workflow optimization, plugin selection, and parameter tuning.
    Optimized for model-specific prompting and token efficiency.
    """

    def __init__(self):
        super().__init__()
        self.client: Optional[AsyncOpenAI] = None
        self.responses_client: Optional[ResponsesAPIClient] = None
        self.default_model = "gpt-4.1-mini"
        self.reasoning_model = "o4-mini"
        self.complex_model = "gpt-4.1"

        # Model categorization for optimal prompting
        self.thinking_models = {"o3", "o4-mini", "o3-mini"}
        self.non_thinking_models = {"gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"}

        # Model-specific pricing for accurate cost calculation
        self.model_pricing = {
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o4-mini": {"input": 1.10, "output": 4.40},
            "o3": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 3.00, "output": 12.00},
        }

    @staticmethod
    def get_name() -> str:
        return "ai_reasoning"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize OpenAI client."""
        self.event_bus = event_bus

        api_key = config.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided in config or environment")

        try:
            self.client = AsyncOpenAI(api_key=api_key)
            self.responses_client = ResponsesAPIClient(api_key)
        except TypeError as e:
            # Fallback for older OpenAI versions
            self.client = AsyncOpenAI(api_key=api_key)
            self.responses_client = ResponsesAPIClient(api_key)

        # Model preferences from config
        models = config.config.get("models", {})
        self.default_model = models.get("default", "gpt-4.1-mini")
        self.reasoning_model = models.get("reasoning", "o4-mini")
        self.complex_model = models.get("complex", "gpt-4.1")

        print(
            f"AI Reasoning initialized with models: {self.default_model}, {self.reasoning_model}, {self.complex_model}"
        )

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute AI reasoning operations."""
        try:
            params = context.state
            action = params.get("action", "reason")

            if action == "reason":
                return await self._reason(params)
            elif action == "optimize_workflow":
                return await self._optimize_workflow(params)
            elif action == "select_plugins":
                return await self._select_plugins(params)
            elif action == "tune_parameters":
                return await self._tune_parameters(params)
            elif action == "analyze_error":
                return await self._analyze_error(params)
            elif action == "generate_recovery_plan":
                return await self._generate_recovery_plan(params)
            else:
                return PluginResult(
                    success=False, error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"AI reasoning error: {str(e)}"
            )

    async def _reason(self, params: Dict[str, Any]) -> PluginResult:
        """General purpose reasoning with context."""
        prompt = params.get("prompt")
        context_data = params.get("context", {})
        model = params.get("model", self.default_model)
        max_tokens = params.get("max_tokens", 1000)

        if not prompt:
            return PluginResult(
                success=False, error_message="Prompt is required for reasoning"
            )

        # Handle object inputs by converting to string
        if isinstance(prompt, dict):
            prompt = json.dumps(prompt, indent=2)
        elif not isinstance(prompt, str):
            prompt = str(prompt)

        # Build context-aware prompt
        full_prompt = self._build_context_prompt(prompt, context_data)

        try:
            # Use structured Responses API client
            system_prompt = self._get_system_prompt(model, "reasoning")

            # Create structured response using ReasoningAnalysis schema
            response_result = await self.responses_client.create_structured_response(
                model=model,
                instructions=system_prompt,
                user_input=full_prompt,
                response_schema=ReasoningAnalysis,
                max_tokens=max_tokens,
                temperature=0.1,
            )

            if response_result["success"]:
                # Successful structured response
                reasoning_data = response_result["data"]

                return PluginResult(
                    success=True,
                    data={
                        "reasoning_steps": reasoning_data["reasoning_steps"],
                        "final_conclusion": reasoning_data["final_conclusion"],
                        "overall_confidence": reasoning_data["overall_confidence"],
                        "key_insights": reasoning_data["key_insights"],
                        "assumptions": reasoning_data["assumptions"],
                        "recommendations": reasoning_data["recommendations"],
                        "model_used": response_result["model"],
                        "model_type": response_result["model_type"],
                        "tokens_used": response_result["usage"],
                        "cost_data": response_result["cost_info"],
                        "context_provided": bool(context_data),
                        "structured_output": True,
                    },
                )
            else:
                # Fallback to unstructured response
                fallback_result = await self.responses_client.create_fallback_response(
                    model=model,
                    instructions=system_prompt,
                    user_input=full_prompt,
                    max_tokens=max_tokens,
                    temperature=0.1,
                )

                if fallback_result["success"]:
                    # Parse fallback response manually
                    raw_content = fallback_result["data"]["response_text"]

                    return PluginResult(
                        success=True,
                        data={
                            "reasoning_steps": [
                                {
                                    "step_number": 1,
                                    "description": "Manual analysis",
                                    "conclusion": raw_content,
                                    "confidence": 0.7,
                                }
                            ],
                            "final_conclusion": raw_content,
                            "overall_confidence": 0.7,
                            "key_insights": ["Unstructured analysis provided"],
                            "assumptions": ["Fallback response used"],
                            "recommendations": ["Review raw output for insights"],
                            "model_used": fallback_result["model"],
                            "model_type": fallback_result["model_type"],
                            "tokens_used": fallback_result["usage"],
                            "cost_data": fallback_result["cost_info"],
                            "context_provided": bool(context_data),
                            "structured_output": False,
                            "fallback_reason": response_result["error"],
                        },
                    )
                else:
                    return PluginResult(
                        success=False,
                        error_message=f"Both structured and fallback responses failed: {response_result['error']}, {fallback_result['error']}",
                    )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"OpenAI API error: {str(e)}"
            )

    async def _optimize_workflow(self, params: Dict[str, Any]) -> PluginResult:
        """Analyze and optimize workflow execution."""
        workflow_definition = params.get("workflow_definition", {})
        execution_history = params.get("execution_history", [])
        available_plugins = params.get("available_plugins", [])

        optimization_prompt = f"""
        WORKFLOW OPTIMIZATION ANALYSIS
        
        Current Workflow:
        {json.dumps(workflow_definition, indent=2)}
        
        Available Plugins:
        {', '.join(available_plugins)}
        
        Recent Execution History:
        {json.dumps(execution_history[-5:], indent=2) if execution_history else "No history available"}
        
        Please analyze this workflow and provide:
        1. Optimization opportunities
        2. Recommended plugin sequence changes
        3. Parameter tuning suggestions
        4. Potential failure points and mitigations
        5. Performance improvement estimates
        
        Format your response as JSON with keys: optimizations, recommended_changes, risk_assessment, estimated_improvement.
        """

        try:
            # Use model-specific prompting for optimization
            system_prompt = self._get_system_prompt(
                self.reasoning_model, "optimization"
            )
            messages = self._build_messages(
                system_prompt, optimization_prompt, self.reasoning_model
            )

            # Use Responses API for workflow optimization with proper format
            system_prompt = self._get_system_prompt(
                self.reasoning_model, "optimization"
            )
            instructions = system_prompt
            user_input = optimization_prompt

            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "workflow_optimization",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "optimizations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of optimization opportunities",
                            },
                            "recommended_changes": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "Specific changes with rationale",
                            },
                            "risk_assessment": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Potential risks and mitigations",
                            },
                            "estimated_improvement": {
                                "type": "string",
                                "description": "Expected performance improvement",
                            },
                            "priority_level": {
                                "type": "string",
                                "description": "High, Medium, or Low priority",
                            },
                        },
                        "required": [
                            "optimizations",
                            "recommended_changes",
                            "risk_assessment",
                            "estimated_improvement",
                            "priority_level",
                        ],
                        "additionalProperties": false,
                    },
                },
            }

            if self.reasoning_model in self.thinking_models:
                response = await self.client.responses.create(
                    model=self.reasoning_model,
                    instructions=instructions,
                    input=user_input,
                    max_completion_tokens=2000,
                    response_format=response_format,
                )
            else:
                response = await self.client.responses.create(
                    model=self.reasoning_model,
                    instructions=instructions,
                    input=user_input,
                    max_tokens=2000,
                    temperature=0.2,
                    response_format=response_format,
                )

            try:
                optimization_data = json.loads(response.output_text)
            except json.JSONDecodeError as e:
                # Fallback for JSON parsing issues
                raw_content = response.output_text
                optimization_data = {
                    "optimizations": ["Raw analysis provided"],
                    "recommended_changes": [
                        {
                            "change": "Review raw output",
                            "rationale": "JSON parsing failed",
                        }
                    ],
                    "risk_assessment": ["Manual review required"],
                    "estimated_improvement": "Unable to parse structured response",
                    "priority_level": "Medium",
                }
            usage = response.usage if hasattr(response, "usage") else None

            return PluginResult(
                success=True,
                data={
                    "optimizations": optimization_data["optimizations"],
                    "recommended_changes": optimization_data["recommended_changes"],
                    "risk_assessment": optimization_data["risk_assessment"],
                    "estimated_improvement": optimization_data["estimated_improvement"],
                    "priority_level": optimization_data["priority_level"],
                    "model_used": self.reasoning_model,
                    "tokens_used": {
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Workflow optimization error: {str(e)}"
            )

    async def _select_plugins(self, params: Dict[str, Any]) -> PluginResult:
        """Intelligently select plugins for a given objective."""
        objective = params.get("objective")
        available_plugins = params.get("available_plugins", [])
        context = params.get("context", {})

        if not objective:
            return PluginResult(
                success=False,
                error_message="Objective is required for plugin selection",
            )

        selection_prompt = f"""
        PLUGIN SELECTION TASK
        
        Objective: {objective}
        
        Available Plugins: {', '.join(available_plugins)}
        
        Context: {json.dumps(context, indent=2)}
        
        Select the optimal sequence of plugins to achieve this objective.
        Consider:
        1. Plugin capabilities and limitations
        2. Data flow between plugins
        3. Error handling and fallbacks
        4. Performance and efficiency
        
        Respond with JSON format:
        {{
            "selected_plugins": ["plugin1", "plugin2", ...],
            "execution_sequence": [
                {{"plugin": "plugin1", "parameters": {{}}, "reasoning": "why this plugin"}},
                ...
            ],
            "risk_factors": ["potential issue 1", ...],
            "success_probability": 0.85
        }}
        """

        try:
            # Use structured outputs for plugin selection
            if self.reasoning_model in self.thinking_models:
                response = await self.client.chat.completions.create(
                    model=self.reasoning_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in plugin orchestration. Select optimal plugin sequences for given objectives.",
                        },
                        {"role": "user", "content": selection_prompt},
                    ],
                    max_completion_tokens=1500,
                    response_format=PluginSelection,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.reasoning_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in plugin orchestration. Select optimal plugin sequences for given objectives.",
                        },
                        {"role": "user", "content": selection_prompt},
                    ],
                    max_tokens=1500,
                    temperature=0.1,
                    response_format=PluginSelection,
                )

            try:
                selection_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                # Fallback for JSON parsing issues
                raw_content = response.choices[0].message.content
                selection_data = {
                    "selected_plugins": ["manual_review_required"],
                    "execution_sequence": [
                        {
                            "plugin": "manual_review",
                            "parameters": {},
                            "reasoning": "JSON parsing failed",
                        }
                    ],
                    "risk_factors": ["Structured output parsing failed"],
                    "success_probability": 0.5,
                    "alternative_approaches": ["Manual plugin selection"],
                }
            usage = response.usage

            return PluginResult(
                success=True,
                data={
                    "selected_plugins": selection_data["selected_plugins"],
                    "execution_sequence": selection_data["execution_sequence"],
                    "risk_factors": selection_data["risk_factors"],
                    "success_probability": selection_data["success_probability"],
                    "alternative_approaches": selection_data["alternative_approaches"],
                    "model_used": self.reasoning_model,
                    "tokens_used": {
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Plugin selection error: {str(e)}"
            )

    async def _tune_parameters(self, params: Dict[str, Any]) -> PluginResult:
        """Optimize plugin parameters based on context."""
        plugin_name = params.get("plugin_name")
        current_parameters = params.get("current_parameters", {})
        execution_context = params.get("execution_context", {})
        performance_history = params.get("performance_history", [])

        tuning_prompt = f"""
        PARAMETER TUNING TASK
        
        Plugin: {plugin_name}
        Current Parameters: {json.dumps(current_parameters, indent=2)}
        Execution Context: {json.dumps(execution_context, indent=2)}
        Performance History: {json.dumps(performance_history[-3:], indent=2) if performance_history else "No history"}
        
        Analyze the current parameters and suggest optimizations based on:
        1. Context requirements
        2. Historical performance
        3. Best practices for this plugin
        4. Resource efficiency
        
        Respond with JSON:
        {{
            "optimized_parameters": {{}},
            "changes_made": [
                {{"parameter": "name", "old_value": "old", "new_value": "new", "reasoning": "why"}}
            ],
            "expected_impact": "description of expected improvements",
            "confidence_score": 0.85
        }}
        """

        try:
            # Use structured outputs for parameter tuning
            if self.default_model in self.thinking_models:
                response = await self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a parameter optimization specialist. Tune plugin parameters for optimal performance.",
                        },
                        {"role": "user", "content": tuning_prompt},
                    ],
                    max_completion_tokens=1200,
                    response_format=ParameterTuning,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a parameter optimization specialist. Tune plugin parameters for optimal performance.",
                        },
                        {"role": "user", "content": tuning_prompt},
                    ],
                    max_tokens=1200,
                    temperature=0.1,
                    response_format=ParameterTuning,
                )

            try:
                tuning_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                # Fallback for JSON parsing issues
                raw_content = response.choices[0].message.content
                tuning_data = {
                    "optimized_parameters": {},
                    "changes_made": [
                        {
                            "parameter": "review_required",
                            "old_value": "unknown",
                            "new_value": "manual_review",
                            "reasoning": "JSON parsing failed",
                        }
                    ],
                    "expected_impact": "Unable to parse structured response",
                    "confidence_score": 0.3,
                    "validation_steps": ["Manual review of raw output"],
                }
            usage = response.usage

            return PluginResult(
                success=True,
                data={
                    "optimized_parameters": tuning_data["optimized_parameters"],
                    "changes_made": tuning_data["changes_made"],
                    "expected_impact": tuning_data["expected_impact"],
                    "confidence_score": tuning_data["confidence_score"],
                    "validation_steps": tuning_data["validation_steps"],
                    "model_used": self.default_model,
                    "tokens_used": {
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Parameter tuning error: {str(e)}"
            )

    async def _analyze_error(self, params: Dict[str, Any]) -> PluginResult:
        """Analyze execution errors and provide insights."""
        error_message = params.get("error_message")
        execution_context = params.get("execution_context", {})
        plugin_name = params.get("plugin_name")
        workflow_state = params.get("workflow_state", {})

        analysis_prompt = f"""
        ERROR ANALYSIS TASK
        
        Error Message: {error_message}
        Failed Plugin: {plugin_name}
        Execution Context: {json.dumps(execution_context, indent=2)}
        Workflow State: {json.dumps(workflow_state, indent=2)}
        
        Analyze this error and provide:
        1. Root cause analysis
        2. Contributing factors
        3. Error classification (temporary, configuration, data, system)
        4. Likelihood of success if retried
        5. Required fixes or workarounds
        
        Respond with JSON:
        {{
            "root_cause": "primary cause",
            "error_type": "temporary|configuration|data|system",
            "retry_recommended": true/false,
            "required_fixes": ["fix1", "fix2"],
            "recovery_strategy": "recommended approach",
            "prevention_measures": ["measure1", "measure2"]
        }}
        """

        try:
            # Use structured outputs for error analysis
            if self.reasoning_model in self.thinking_models:
                response = await self.client.chat.completions.create(
                    model=self.reasoning_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in error analysis and system debugging. Provide thorough error analysis and recovery recommendations.",
                        },
                        {"role": "user", "content": analysis_prompt},
                    ],
                    max_completion_tokens=1500,
                    response_format=ErrorAnalysis,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.reasoning_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in error analysis and system debugging. Provide thorough error analysis and recovery recommendations.",
                        },
                        {"role": "user", "content": analysis_prompt},
                    ],
                    max_tokens=1500,
                    temperature=0.1,
                    response_format=ErrorAnalysis,
                )

            try:
                analysis_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                # Fallback for JSON parsing issues
                raw_content = response.choices[0].message.content
                analysis_data = {
                    "root_cause": "JSON parsing failed",
                    "error_type": "system",
                    "retry_recommended": True,
                    "required_fixes": ["Review structured output implementation"],
                    "recovery_strategy": "Manual error analysis",
                    "prevention_measures": ["Improve JSON parsing robustness"],
                }
            usage = response.usage

            return PluginResult(
                success=True,
                data={
                    "root_cause": analysis_data["root_cause"],
                    "error_type": analysis_data["error_type"],
                    "retry_recommended": analysis_data["retry_recommended"],
                    "required_fixes": analysis_data["required_fixes"],
                    "recovery_strategy": analysis_data["recovery_strategy"],
                    "prevention_measures": analysis_data["prevention_measures"],
                    "model_used": self.reasoning_model,
                    "tokens_used": {
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Error analysis failed: {str(e)}"
            )

    async def _generate_recovery_plan(self, params: Dict[str, Any]) -> PluginResult:
        """Generate intelligent recovery plan for failed workflows."""
        failure_details = params.get("failure_details", {})
        workflow_definition = params.get("workflow_definition", {})
        available_plugins = params.get("available_plugins", [])

        recovery_prompt = f"""
        RECOVERY PLAN GENERATION
        
        Failure Details: {json.dumps(failure_details, indent=2)}
        Original Workflow: {json.dumps(workflow_definition, indent=2)}
        Available Plugins: {', '.join(available_plugins)}
        
        Generate a comprehensive recovery plan that includes:
        1. Immediate recovery steps
        2. Alternative workflow paths
        3. Data recovery if needed
        4. Prevention of similar failures
        5. Monitoring and validation steps
        
        Respond with JSON:
        {{
            "immediate_actions": ["action1", "action2"],
            "alternative_workflow": {{
                "steps": [...],
                "reasoning": "why this approach"
            }},
            "data_recovery_needed": true/false,
            "validation_steps": ["check1", "check2"],
            "estimated_success_rate": 0.85,
            "estimated_recovery_time": "5 minutes"
        }}
        """

        try:
            # Use structured outputs for recovery planning
            if self.complex_model in self.thinking_models:
                response = await self.client.chat.completions.create(
                    model=self.complex_model,  # Use complex model for recovery planning
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a disaster recovery specialist for automated workflows. Generate comprehensive recovery plans.",
                        },
                        {"role": "user", "content": recovery_prompt},
                    ],
                    max_completion_tokens=2000,
                    response_format=RecoveryPlan,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.complex_model,  # Use complex model for recovery planning
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a disaster recovery specialist for automated workflows. Generate comprehensive recovery plans.",
                        },
                        {"role": "user", "content": recovery_prompt},
                    ],
                    max_tokens=2000,
                    temperature=0.2,
                    response_format=RecoveryPlan,
                )

            try:
                recovery_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                # Fallback for JSON parsing issues
                raw_content = response.choices[0].message.content
                recovery_data = {
                    "immediate_actions": ["Manual review required"],
                    "alternative_workflow": {
                        "steps": ["manual_intervention"],
                        "reasoning": "JSON parsing failed",
                    },
                    "data_recovery_needed": False,
                    "validation_steps": ["Review raw output"],
                    "estimated_success_rate": 0.5,
                    "estimated_recovery_time": "Manual review time",
                }
            usage = response.usage

            return PluginResult(
                success=True,
                data={
                    "immediate_actions": recovery_data["immediate_actions"],
                    "alternative_workflow": recovery_data["alternative_workflow"],
                    "data_recovery_needed": recovery_data["data_recovery_needed"],
                    "validation_steps": recovery_data["validation_steps"],
                    "estimated_success_rate": recovery_data["estimated_success_rate"],
                    "estimated_recovery_time": recovery_data["estimated_recovery_time"],
                    "model_used": self.complex_model,
                    "tokens_used": {
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            return PluginResult(
                success=False,
                error_message=f"Recovery plan generation failed: {str(e)}",
            )

    def _build_context_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build context-aware prompt."""
        if not context:
            return prompt

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"Context:\n{context_str}\n\nTask: {prompt}"

    def _get_system_prompt(self, model: str, task_type: str) -> str:
        """Generate model-specific system prompts with detailed roles and expertise."""
        if model in self.thinking_models:
            # Thinking models: General guidance, let them reason
            return self._get_thinking_model_prompt(task_type)
        else:
            # Non-thinking models: Specific detailed instructions
            return self._get_non_thinking_model_prompt(task_type)

    def _get_thinking_model_prompt(self, task_type: str) -> str:
        """System prompts optimized for thinking models (o3, o4-mini, etc.)."""
        base_prompt = """You are an expert workflow orchestration architect with deep experience in distributed systems, automation frameworks, and intelligent process optimization.

Your expertise spans:
- 15+ years in enterprise workflow design and optimization
- Deep knowledge of microservices, event-driven architectures, and automation patterns
- Proven track record in reducing operational costs and improving system reliability
- Expert in failure analysis, recovery planning, and preventive system design

Approach each task with systematic thinking and evidence-based recommendations."""

        if task_type == "reasoning":
            return (
                base_prompt
                + "\n\nFocus on providing clear, actionable insights with supporting rationale."
            )
        elif task_type == "optimization":
            return (
                base_prompt
                + "\n\nAnalyze thoroughly and provide specific optimization strategies with measurable impact predictions."
            )
        elif task_type == "error_analysis":
            return (
                base_prompt
                + "\n\nPerform comprehensive root cause analysis with systematic recovery recommendations."
            )
        else:
            return base_prompt

    def _get_non_thinking_model_prompt(self, task_type: str) -> str:
        """System prompts optimized for non-thinking models (GPT-4.1, etc.) with specific instructions."""
        base_prompt = """You are a Senior Workflow Orchestration Specialist with the following specific qualifications:

ROLE: Lead Automation Architect
EXPERIENCE: 12+ years in enterprise workflow systems
EXPERTISE:
- Distributed system design and microservices orchestration
- Performance optimization and cost reduction strategies
- Error handling, retry mechanisms, and fault tolerance
- Plugin architecture and modular system design
- Real-time monitoring and predictive analytics

SKILLS:
- Technical: Python, async programming, REST APIs, message queues
- Analytical: Root cause analysis, performance profiling, bottleneck identification
- Strategic: Cost-benefit analysis, risk assessment, capacity planning

APPROACH:
1. Always provide structured, actionable recommendations
2. Include specific implementation details and examples
3. Quantify expected improvements where possible
4. Consider both immediate and long-term implications
5. Address potential risks and mitigation strategies"""

        if task_type == "reasoning":
            return (
                base_prompt
                + "\n\nINSTRUCTIONS: Provide clear reasoning with step-by-step analysis. Structure your response with numbered points and specific recommendations."
            )
        elif task_type == "optimization":
            return (
                base_prompt
                + "\n\nINSTRUCTIONS: Analyze the workflow systematically. Provide specific optimization recommendations with estimated performance improvements and implementation steps."
            )
        elif task_type == "error_analysis":
            return (
                base_prompt
                + "\n\nINSTRUCTIONS: Perform structured error analysis. Identify root cause, contributing factors, and provide detailed recovery plan with prevention measures."
            )
        else:
            return (
                base_prompt
                + "\n\nINSTRUCTIONS: Provide detailed, structured analysis with specific actionable recommendations."
            )

    def _build_messages(
        self, system_prompt: str, user_prompt: str, model: str
    ) -> List[Dict[str, str]]:
        """Build message array optimized for model type."""
        if model in self.thinking_models:
            # Thinking models: Simple message structure
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        else:
            # Non-thinking models: May benefit from examples or additional structure
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

    async def _call_responses_api(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        response_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Helper method to call OpenAI Responses API with consistent error handling."""
        instructions = system_prompt
        user_input = user_prompt

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema["name"],
                "schema": response_schema["schema"],
            },
        }

        try:
            # Use Responses API with appropriate parameters for model type
            if model in self.thinking_models:
                # Thinking models: use max_completion_tokens, no custom temperature
                response = await self.client.responses.create(
                    model=model,
                    instructions=instructions,
                    input=user_input,
                    max_completion_tokens=max_tokens,
                    response_format=response_format,
                )
            else:
                # Non-thinking models: use max_tokens with temperature
                response = await self.client.responses.create(
                    model=model,
                    instructions=instructions,
                    input=user_input,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    response_format=response_format,
                )

            # Parse response from Responses API
            try:
                parsed_data = json.loads(response.output_text)
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                parsed_data = {
                    "error": "JSON parsing failed",
                    "raw_content": response.output_text,
                }

            # Get usage data from response
            usage = response.usage if hasattr(response, "usage") else None

            return {
                "success": True,
                "data": parsed_data,
                "usage": usage,
                "model": model,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "model": model}

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> Dict[str, Any]:
        """Calculate actual cost based on input and output tokens."""
        if model not in self.model_pricing:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "note": f"Pricing not available for model {model}",
            }

        pricing = self.model_pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "model": model,
        }

    def get_optimal_model_for_task(
        self, task_type: str, complexity: str = "medium"
    ) -> str:
        """Select optimal model based on task type and complexity."""
        if task_type in ["reasoning", "analysis", "optimization"]:
            if complexity == "high":
                return "o4-mini"  # Thinking model for complex reasoning
            else:
                return "gpt-4.1-mini"  # Efficient for standard tasks
        elif task_type in ["simple_classification", "formatting", "extraction"]:
            return "gpt-4.1-nano"  # Most cost-effective
        elif task_type in ["creative", "planning", "strategy"]:
            return "gpt-4.1"  # Flagship model for complex creative tasks
        else:
            return self.default_model

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()
        if self.responses_client:
            await self.responses_client.close()

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="reason", description="General purpose AI reasoning with context"
            ),
            Capability(
                name="optimize_workflow",
                description="Analyze and optimize workflow execution patterns",
            ),
            Capability(
                name="select_plugins",
                description="Intelligently select optimal plugins for objectives",
            ),
            Capability(
                name="tune_parameters",
                description="Optimize plugin parameters based on context and history",
            ),
            Capability(
                name="analyze_error",
                description="Analyze execution errors and provide insights",
            ),
            Capability(
                name="generate_recovery_plan",
                description="Generate intelligent recovery plans for failed workflows",
            ),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data."""
        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def get_dependencies() -> List[str]:
        """External dependencies."""
        return ["openai", "pydantic"]

    @staticmethod
    def get_configuration_schema() -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "openai_api_key": {"type": "string"},
                "models": {
                    "type": "object",
                    "properties": {
                        "default": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "complex": {"type": "string"},
                    },
                },
            },
            "required": ["openai_api_key"],
        }
