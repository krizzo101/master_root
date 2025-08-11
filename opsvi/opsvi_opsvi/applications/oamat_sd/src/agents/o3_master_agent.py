"""
O3 Master Agent - Modular Implementation

A clean, modular orchestrator for O3-powered reasoning and analysis.
Coordinates specialized modules for complexity analysis, strategy generation, and execution planning.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.applications.oamat_sd.src.agents.request_validation import (
    CompletionResult,
    ValidationResult,
)
from src.applications.oamat_sd.src.analysis.complexity_analyzer import (
    ComplexityAnalyzer,
)
from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.education.o3_framework_educator import (
    O3FrameworkEducator,
)
from src.applications.oamat_sd.src.models.o3_analysis_models import (
    AnalysisType,
    O3AnalysisResult,
    PipelineDesign,
    ReasoningStep,
)
from src.applications.oamat_sd.src.reasoning.ai_reasoning_utils import AIReasoningUtils
from src.applications.oamat_sd.src.strategy.strategy_generator import StrategyGenerator


class O3MasterAgent:
    """
    Modular O3 Master Agent with Advanced Reasoning

    This agent orchestrates the complete O3 analysis workflow:
    1. Complexity Analysis -> Assess request complexity
    2. Strategy Generation -> Generate agent deployment strategy
    3. Execution Planning -> Create detailed execution plans
    4. Pipeline Design -> Design optimal workflows
    5. Comprehensive Analysis -> Combine all results
    """

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """Initialize the O3 Master Agent with all modular components"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize core AI reasoning utilities
        self.ai_reasoning = AIReasoningUtils(model_config)

        # Initialize specialized modules
        self.complexity_analyzer = ComplexityAnalyzer()
        self.strategy_generator = StrategyGenerator(self.ai_reasoning)

        self.framework_educator = O3FrameworkEducator()

        # Store reasoning history for analysis
        self.reasoning_history: List[ReasoningStep] = []

        self.logger.info("✅ O3 Master Agent initialized with modular architecture")

    async def analyze_request_complexity(
        self, request: Dict[str, Any], validation_result: ValidationResult
    ) -> Tuple[any, List[ReasoningStep]]:
        """Delegate complexity analysis to specialized module"""
        self.logger.info("🧠 Delegating to Complexity Analyzer...")

        (
            complexity_result,
            reasoning_steps,
        ) = await self.complexity_analyzer.analyze_request_complexity(
            request, validation_result
        )

        # Store reasoning steps
        self.reasoning_history.extend(reasoning_steps)

        return complexity_result, reasoning_steps

    async def generate_agent_strategy(
        self, complexity_result, completion_result: CompletionResult
    ) -> Tuple[any, List[ReasoningStep]]:
        """Delegate strategy generation to specialized module"""
        self.logger.info("🎯 Delegating to Strategy Generator...")

        (
            agent_strategy,
            reasoning_steps,
        ) = await self.strategy_generator.generate_agent_strategy(
            complexity_result, completion_result
        )

        # Store reasoning steps
        self.reasoning_history.extend(reasoning_steps)

        return agent_strategy, reasoning_steps

    async def generate_execution_plan(
        self, strategy, request_data: Dict[str, Any]
    ) -> Tuple[any, List[ReasoningStep]]:
        """Delegate execution planning to specialized module"""
        self.logger.info("📋 Delegating to Strategy Generator for execution planning...")

        (
            execution_plan,
            reasoning_steps,
        ) = await self.strategy_generator.generate_execution_plan(
            strategy, request_data
        )

        # Store reasoning steps
        self.reasoning_history.extend(reasoning_steps)

        return execution_plan, reasoning_steps

    async def design_optimal_pipeline(
        self, request_data: Dict[str, Any], context: Dict[str, Any] = None
    ) -> Tuple[PipelineDesign, List[ReasoningStep]]:
        """
        Meta-pipeline design: O3 determines optimal pipeline structure for this specific request.
        NO ASSUMPTIONS about stages - O3 decides what pipeline is needed.
        """
        self.logger.info(
            "🏗️ O3 Meta-Pipeline Design: Determining optimal pipeline structure"
        )

        reasoning_steps = []

        # Step 1: Request analysis and pipeline design
        step1 = ReasoningStep(
            step_id="meta_pipeline_design",
            analysis_type=AnalysisType.STRATEGY,
            reasoning="Analyzing request to determine optimal pipeline structure",
            confidence=0.9,
            evidence=[
                f"Request content: {(request_data.get('content') if 'content' in request_data else ConfigManager().analysis.request_processing['default_empty_content'])[:200]}...",
                f"Context available: {bool(context)}",
                f"Request type: {request_data.get('type') if 'type' in request_data else ConfigManager().analysis.request_processing['unknown_type']}",
            ],
        )
        reasoning_steps.append(step1)

        # Create comprehensive pipeline design prompt
        framework_knowledge = (
            self.framework_educator.get_comprehensive_framework_knowledge()
        )

        design_prompt = f"""
        Analyze this request and design the optimal pipeline structure:

        REQUEST ANALYSIS:
        - Content: {request_data.get('content') if 'content' in request_data else ConfigManager().analysis.request_processing['default_empty_content']}
        - Type: {request_data.get('type') if 'type' in request_data else ConfigManager().analysis.request_processing['unknown_type']}
        - Context: {context or {}}

        FRAMEWORK KNOWLEDGE:
        - Available Tools: {list(framework_knowledge['tool_catalog'].keys())}
        - Execution Patterns: {list(framework_knowledge['framework_architecture']['execution_patterns'].keys())}
        - Best Practices: {framework_knowledge['best_practices']['dynamic_generation']['principles']}

        DESIGN REQUIREMENTS:
        1. Determine optimal pipeline type (linear, parallel, conditional, hybrid)
        2. Define pipeline stages with clear dependencies
        3. Design execution graph with proper coordination
        4. Specify context management requirements
        5. Provide optimization rationale

        OUTPUT FORMAT (JSON):
        {{
            "pipeline_type": "linear|parallel|conditional|hybrid",
            "stages": [
                {{
                    "stage_id": "unique_identifier",
                    "name": "descriptive_stage_name",
                    "description": "stage_purpose_and_function",
                    "dependencies": ["prerequisite_stage_ids"],
                    "parallel_compatible": true/false,
                    "execution_mode": "sequential|parallel|conditional",
                    "context_requirements": ["required_context_from_previous_stages"],
                    "outputs": ["stage_output_specifications"]
                }}
            ],
            "execution_graph": {{
                "nodes": ["stage_identifiers"],
                "edges": [["from_stage", "to_stage"]],
                "parallel_groups": [["stage1", "stage2"]],
                "synchronization_points": ["sync_stage_ids"]
            }},
            "context_management": {{
                "state_flow": "how_state_flows_between_stages",
                "context_preservation": "how_context_is_maintained",
                "synchronization_strategy": "how_parallel_stages_sync",
                "error_recovery": "how_failures_are_handled"
            }},
            "optimization_rationale": "explanation_of_design_decisions",
            "estimated_efficiency": "performance_expectations",
            "alternative_approaches": ["other_viable_designs"]
        }}

        Design the most effective pipeline for this specific request.
        """

        try:
            # Call O3 for meta-pipeline design
            response_content = await self.ai_reasoning.call_ai_reasoning(
                design_prompt, "Meta-Pipeline Design"
            )

            # Parse O3 response
            pipeline_data = self.ai_reasoning.parse_json_from_ai_response(
                response_content, "PipelineDesign"
            )

            # Step 2: Pipeline validation and assembly
            step2 = ReasoningStep(
                step_id="pipeline_validation",
                analysis_type=AnalysisType.STRATEGY,
                reasoning=f"Validated and assembled optimal pipeline with {len(pipeline_data['stages'])} stages",
                confidence=0.85,
                evidence=[
                    f"Pipeline type: {pipeline_data.get('pipeline_type') if 'pipeline_type' in pipeline_data else ConfigManager().analysis.request_processing['undefined_status']}",
                    f"Stages: {len(pipeline_data.get('stages') if 'stages' in pipeline_data else [])}",
                    f"Parallel groups: {len(pipeline_data['execution_graph']['parallel_groups']) if 'execution_graph' in pipeline_data and 'parallel_groups' in pipeline_data['execution_graph'] else 0}",
                ],
            )
            reasoning_steps.append(step2)

            # Convert to PipelineDesign object
            pipeline_design = PipelineDesign(
                pipeline_type=pipeline_data["pipeline_type"],
                stages=pipeline_data["stages"],
                execution_graph=pipeline_data["execution_graph"],
                context_management=pipeline_data["context_management"],
                optimization_rationale=(
                    pipeline_data.get("optimization_rationale")
                    if "optimization_rationale" in pipeline_data
                    else ConfigManager().analysis.request_processing[
                        "default_empty_content"
                    ]
                ),
                estimated_efficiency=(
                    pipeline_data.get("estimated_efficiency")
                    if "estimated_efficiency" in pipeline_data
                    else ConfigManager().analysis.request_processing[
                        "default_empty_content"
                    ]
                ),
                alternative_approaches=(
                    pipeline_data.get("alternative_approaches")
                    if "alternative_approaches" in pipeline_data
                    else []
                ),
            )

            # Store reasoning steps
            self.reasoning_history.extend(reasoning_steps)

            self.logger.info(
                f"✅ Optimal pipeline designed: {pipeline_design.pipeline_type}"
            )
            return pipeline_design, reasoning_steps

        except Exception as e:
            self.logger.error(f"Pipeline design failed: {e}")
            raise RuntimeError(
                f"Meta-pipeline design failed: {e}. Cannot proceed without optimal pipeline structure."
            )

    async def perform_comprehensive_analysis(
        self,
        request: Dict[str, Any],
        validation_result: ValidationResult,
        completion_result: CompletionResult,
    ) -> O3AnalysisResult:
        """Perform complete O3-level analysis and planning by orchestrating all modules"""
        self.logger.info(
            "🎯 Performing comprehensive O3 analysis - orchestrating all modules"
        )

        try:
            # Step 1: Complexity analysis
            self.logger.info("📊 Step 1: Complexity Analysis")
            (
                complexity_result,
                complexity_reasoning,
            ) = await self.analyze_request_complexity(request, validation_result)

            # Step 2: Strategy generation
            self.logger.info("🎯 Step 2: Agent Strategy Generation")
            agent_strategy, strategy_reasoning = await self.generate_agent_strategy(
                complexity_result, completion_result
            )

            # Step 3: Execution planning
            self.logger.info("📋 Step 3: Execution Planning")
            execution_plan, plan_reasoning = await self.generate_execution_plan(
                agent_strategy, request
            )

            # Step 4: Compile comprehensive analysis
            self.logger.info("🔄 Step 4: Analysis Synthesis")

            # Combine all reasoning steps
            all_reasoning = []
            all_reasoning.extend(complexity_reasoning)
            all_reasoning.extend(strategy_reasoning)
            all_reasoning.extend(plan_reasoning)

            # Create comprehensive analysis result
            analysis_result = O3AnalysisResult(
                request_analysis={
                    "request_type": validation_result.request_type,
                    "extracted_info": validation_result.extracted_info,
                    "completion_status": completion_result.completion_status,
                },
                complexity_assessment=complexity_result,
                agent_strategy=agent_strategy,
                execution_plan=execution_plan,
                reasoning_chain=all_reasoning,
                confidence=sum(step.confidence for step in all_reasoning)
                / len(all_reasoning),
                recommendations=[
                    f"Use {complexity_result.execution_strategy} execution strategy",
                    f"Deploy {len(agent_strategy.agent_roles)} specialized agents",
                    f"Execute in {len(execution_plan.phases)} phases",
                    f"Estimated effort: {complexity_result.estimated_effort}",
                ],
            )

            self.logger.info(
                f"✅ Comprehensive O3 analysis complete - confidence: {analysis_result.confidence:.2f}"
            )
            return analysis_result

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            raise RuntimeError(
                f"O3 comprehensive analysis failed: {e}. Cannot proceed without complete analysis."
            )

    def get_reasoning_history(self) -> List[ReasoningStep]:
        """Get the complete reasoning history for analysis"""
        return self.reasoning_history.copy()

    def clear_reasoning_history(self):
        """Clear the reasoning history"""
        self.reasoning_history.clear()
        self.logger.info("🧹 Reasoning history cleared")

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this O3 master agent"""
        return {
            "agent_name": "O3 Master Agent",
            "version": "2.0.0-modular",
            "architecture": "modular",
            "components": {
                "complexity_analyzer": "O3-powered complexity assessment",
                "strategy_generator": "Dynamic agent strategy generation",
                "ai_reasoning_utils": "AI reasoning infrastructure",
                "framework_educator": "Comprehensive framework knowledge",
            },
            "capabilities": [
                "Advanced complexity analysis with O3 reasoning",
                "Dynamic agent strategy generation",
                "Sophisticated execution planning",
                "Meta-pipeline design",
                "Comprehensive multi-dimensional analysis",
                "Context-aware reasoning and planning",
            ],
            "models_used": ["o3-mini", "gpt-4.1-mini"],
            "reasoning_history_tracking": True,
            "modular_architecture": True,
        }
