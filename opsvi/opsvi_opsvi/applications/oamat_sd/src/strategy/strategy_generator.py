"""
Strategy Generator Module

Handles O3-powered agent strategy generation and execution planning.
Extracted from o3_master_agent.py for better modularity.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from src.applications.oamat_sd.src.agents.request_validation import CompletionResult
from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.education.o3_framework_educator import (
    O3FrameworkEducator,
)
from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityAnalysisResult,
    ExecutionStrategy,
)
from src.applications.oamat_sd.src.models.o3_analysis_models import (
    AgentStrategy,
    AnalysisType,
    ExecutionPlan,
    ReasoningStep,
)


class StrategyGenerator:
    """Handles O3-powered strategy generation and execution planning"""

    def __init__(self, ai_reasoning_utils):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.ai_reasoning_utils = ai_reasoning_utils
        self.framework_educator = O3FrameworkEducator()

    async def generate_agent_strategy(
        self,
        complexity_result: ComplexityAnalysisResult,
        completion_result: CompletionResult,
    ) -> Tuple[AgentStrategy, List[ReasoningStep]]:
        """Generate sophisticated agent deployment strategy."""

        self.logger.info(
            f"Generating agent strategy for {complexity_result.execution_strategy} execution"
        )

        reasoning_steps = []

        # Step 1: Strategy selection reasoning
        step1 = ReasoningStep(
            step_id="strategy_selection",
            analysis_type=AnalysisType.STRATEGY,
            reasoning=f"Selected {complexity_result.execution_strategy} based on complexity score {complexity_result.overall_score}",
            confidence=ConfigManager().reasoning.high_confidence_score,
            evidence=[
                f"Complexity: {complexity_result.overall_score}",
                f"Strategy: {complexity_result.execution_strategy}",
            ],
        )
        reasoning_steps.append(step1)

        # Step 2: Dynamic strategy generation using O3
        framework_context = (
            self.framework_educator.get_comprehensive_framework_knowledge()
        )

        strategy_prompt = f"""
        You are an expert system architect designing optimal multi-agent workflows.

        ## REQUEST ANALYSIS
        **Complexity Score**: {complexity_result.overall_score}/10
        **Category**: {complexity_result.category}
        **Recommended Strategy**: {complexity_result.execution_strategy}

        ## FRAMEWORK CONTEXT
        **Available Tools**: {list(framework_context['tool_catalog'].keys())}
        **Execution Patterns**: {list(framework_context['framework_architecture']['execution_patterns'].keys())}

        ## AGENT STRATEGY REQUIREMENTS
        Design a comprehensive agent strategy with:

        1. **Agent Specialization**: Define 2-5 specialized agents based on complexity
        2. **Tool Assignment**: Assign specific tools to each agent
        3. **Coordination Pattern**: Define how agents will coordinate
        4. **Success Criteria**: Clear, measurable success criteria

        ## OUTPUT FORMAT (JSON)
        ```json
        {{
            "execution_strategy": "simple|multi_agent|orchestrated",
            "agent_roles": [
                {{
                    "role": "Agent Role Name",
                    "description": "Agent capabilities and responsibilities",
                    "tools": ["tool1", "tool2", "tool3"],
                    "deliverables": ["specific_file_names"],
                    "success_criteria": ["measurable_criteria"]
                }}
            ],
            "coordination_pattern": "sequential|parallel|hybrid",
            "communication_flow": {{"agent1": ["agent2", "agent3"]}},
            "success_criteria": ["overall_project_criteria"],
            "risk_mitigation": ["mitigation_strategies"]
        }}
        ```

        Generate the optimal strategy for this specific request.
        """

        step2 = ReasoningStep(
            step_id="dynamic_strategy_generation",
            analysis_type=AnalysisType.STRATEGY,
            reasoning="Using O3 reasoning to generate dynamic, context-specific agent strategy",
            confidence=ConfigManager().reasoning.high_confidence_score,
            evidence=[
                f"Request complexity: {complexity_result.overall_score}/10",
                f"Framework tools available: {len(framework_context['tool_catalog'])}",
                "Dynamic analysis based on specific request requirements",
            ],
        )
        reasoning_steps.append(step2)

        try:
            # Call O3 for dynamic strategy generation
            response_content = await self.ai_reasoning_utils.call_ai_reasoning(
                strategy_prompt, "Stage 2: Dynamic Agent Strategy Generation"
            )

            # Parse O3 response
            strategy_data = self._parse_strategy_response(response_content)

            # Step 3: Strategy validation and assembly

            step3 = ReasoningStep(
                step_id="strategy_validation",
                analysis_type=AnalysisType.STRATEGY,
                reasoning=f"Validated and assembled dynamic strategy with {len(strategy_data['agent_roles'])} specialized agents",
                confidence=ConfigManager().reasoning.default_confidence_score,
                evidence=[
                    f"Agent roles: {[role['role'] for role in strategy_data['agent_roles']]}",
                    f"Coordination: {strategy_data['coordination_pattern']}",
                    f"Execution strategy: {strategy_data['execution_strategy']}",
                ],
            )
            reasoning_steps.append(step3)

            # Convert to AgentStrategy object
            agent_strategy = self._build_agent_strategy_from_o3(
                strategy_data, complexity_result
            )

            return agent_strategy, reasoning_steps

        except Exception as e:
            self.logger.error(f"Dynamic strategy generation failed: {e}")
            # NO FALLBACKS - fail completely if O3 generation fails
            raise RuntimeError(
                f"Stage 2 dynamic agent strategy generation failed: {e}. System cannot proceed without O3 analysis."
            )

    async def generate_execution_plan(
        self, strategy: AgentStrategy, request_data: Dict[str, Any]
    ) -> Tuple[ExecutionPlan, List[ReasoningStep]]:
        """Generate detailed execution plan using O3 reasoning."""

        self.logger.info("Generating detailed execution plan using O3 reasoning")

        reasoning_steps = []

        # Step 1: Plan generation reasoning
        step1 = ReasoningStep(
            step_id="execution_planning",
            analysis_type=AnalysisType.PLANNING,
            reasoning=f"Generating execution plan for {strategy.execution_strategy} strategy with {len(strategy.agent_roles)} agents",
            confidence=ConfigManager().reasoning.medium_confidence_score,
            evidence=[
                f"Strategy: {strategy.execution_strategy}",
                f"Agents: {len(strategy.agent_roles)}",
                f"Coordination: {strategy.coordination_pattern}",
            ],
        )
        reasoning_steps.append(step1)

        # Generate AI-driven execution plan
        plan_prompt = f"""
        Create a detailed execution plan for this agent strategy:

        ## AGENT STRATEGY
        **Execution Strategy**: {strategy.execution_strategy}
        **Agent Roles**: {strategy.agent_roles}
        **Coordination**: {strategy.coordination_pattern}

        ## PLAN REQUIREMENTS
        Generate a comprehensive execution plan with:

        1. **Phases**: Logical execution phases with dependencies
        2. **Dependencies**: Clear dependency mapping between phases
        3. **Resources**: Resource requirements for each phase
        4. **Timelines**: Realistic timeline estimates
        5. **Quality Gates**: Validation checkpoints
        6. **Parallel Opportunities**: Tasks that can run concurrently
        7. **Sequential Requirements**: Tasks that must run in sequence

        ## OUTPUT FORMAT (JSON)
        ```json
        {{
            "phases": [
                {{
                    "name": "phase_name",
                    "description": "phase_description",
                    "duration": "time_estimate",
                    "agents_involved": ["agent_roles"],
                    "deliverables": ["file_names"],
                    "dependencies": ["prerequisite_phases"]
                }}
            ],
            "dependencies": {{"phase1": ["prerequisite1", "prerequisite2"]}},
            "resource_requirements": {{"agents": 3, "tools": ["tool_list"]}},
            "timeline_estimates": {{"phase1": "duration", "phase2": "duration"}},
            "quality_gates": ["validation_checkpoints"],
            "parallel_opportunities": [
                {{
                    "phases": ["phase1", "phase2"],
                    "rationale": "why_parallel_safe"
                }}
            ],
            "sequential_requirements": [
                {{
                    "sequence": ["phase1", "phase2"],
                    "rationale": "why_sequence_required"
                }}
            ],
            "integration_points": ["context_transfer_points"],
            "consistency_checks": ["validation_points"]
        }}
        ```

        Generate the optimal execution plan.
        """

        try:
            # Call AI reasoning for plan generation
            response_content = await self.ai_reasoning_utils.call_ai_reasoning(
                plan_prompt, "Execution Plan Generation"
            )

            # Parse AI response
            plan_data = self.ai_reasoning_utils.parse_json_from_ai_response(
                response_content, "ExecutionPlan"
            )

            # Step 2: Plan validation
            step2 = ReasoningStep(
                step_id="plan_validation",
                analysis_type=AnalysisType.PLANNING,
                reasoning=f"Generated and validated execution plan with {len(plan_data['phases'])} phases",
                confidence=ConfigManager().reasoning.high_confidence_score,
                evidence=[
                    f"Phases: {len(plan_data['phases'])}",
                    f"Parallel opportunities: {len(plan_data['parallel_opportunities'])}",  # Will KeyError if missing - NO FALLBACKS
                    f"Sequential requirements: {len(plan_data['sequential_requirements'])}",  # Will KeyError if missing - NO FALLBACKS
                    f"AI reasoning: {plan_data['reasoning']}",  # Will KeyError if missing - NO FALLBACKS
                ],
            )
            reasoning_steps.append(step2)

            # Convert AI output to ExecutionPlan object
            execution_plan = ExecutionPlan(
                phases=plan_data["phases"],
                dependencies=plan_data["dependencies"],
                resource_requirements=plan_data["resource_requirements"],
                timeline_estimates=plan_data["timeline_estimates"],
                quality_gates=plan_data["quality_gates"],
                contingency_plans=[
                    "AI-determined fallback strategies",
                    "Dynamic error recovery",
                    "Resource reallocation protocols",
                ],
                parallel_opportunities=plan_data[
                    "parallel_opportunities"
                ],  # NO FALLBACKS - will KeyError if missing
                sequential_requirements=plan_data[
                    "sequential_requirements"
                ],  # NO FALLBACKS - will KeyError if missing
                integration_points=plan_data[
                    "integration_points"
                ],  # NO FALLBACKS - will KeyError if missing
                consistency_checks=plan_data[
                    "consistency_checks"
                ],  # NO FALLBACKS - will KeyError if missing
            )

            self.logger.info(
                f"✅ AI-driven execution plan created with {len(execution_plan.phases)} phases"
            )
            return execution_plan, reasoning_steps

        except Exception as e:
            self.logger.error(f"Execution plan generation failed: {e}")
            raise RuntimeError(
                f"Execution plan generation failed: {e}. Cannot proceed without valid plan."
            )

    def _parse_strategy_response(self, response_content: str) -> Dict[str, Any]:
        """Parse O3 strategy response and extract structured data"""
        try:
            # Look for JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                strategy_json = json_match.group()
                return json.loads(strategy_json)
            else:
                raise ValueError("No JSON found in O3 response")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse O3 strategy response: {e}")
            self.logger.error(f"Raw response content: {response_content}")
            # NO FALLBACKS - fail completely if O3 response cannot be parsed
            raise RuntimeError(
                f"O3 strategy response parsing failed: {e}. System cannot proceed without valid O3 analysis. "
                f"Raw response: {response_content[:500]}..."
            )

    def _build_agent_strategy_from_o3(
        self, strategy_data: Dict[str, Any], complexity_result: ComplexityAnalysisResult
    ) -> AgentStrategy:
        """Build AgentStrategy object from O3's dynamic response"""

        # Extract agent roles from O3 response - NO FALLBACKS
        agent_roles = []
        for role_data in strategy_data["agent_roles"]:  # Will KeyError if missing
            agent_roles.append(role_data["role"])  # Will KeyError if missing

        # Determine execution strategy
        execution_strategy_map = {
            "simple": ExecutionStrategy.SIMPLE,
            "multi_agent": ExecutionStrategy.MULTI_AGENT,
            "orchestrated": ExecutionStrategy.ORCHESTRATED,
        }
        # Get execution strategy without fallbacks
        execution_strategy_key = strategy_data[
            "execution_strategy"
        ]  # Will KeyError if missing
        if execution_strategy_key not in execution_strategy_map:
            raise RuntimeError(
                f"Unknown execution strategy: {execution_strategy_key} - NO FALLBACKS ALLOWED"
            )
        execution_strategy = execution_strategy_map[execution_strategy_key]

        # Build AgentStrategy object - NO FALLBACKS
        return AgentStrategy(
            execution_strategy=execution_strategy,
            agent_roles=agent_roles,
            coordination_pattern=strategy_data[
                "coordination_pattern"
            ],  # Will KeyError if missing
            communication_flow=strategy_data[
                "communication_flow"
            ],  # Will KeyError if missing
            success_criteria=strategy_data[
                "success_criteria"
            ],  # Will KeyError if missing
            risk_mitigation=strategy_data[
                "risk_mitigation"
            ],  # Will KeyError if missing
        )
