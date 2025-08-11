"""Planner agent for the autonomous software factory."""

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from opsvi_auto_forge.agents.base_agent import AgentResponse, BaseAgent
from opsvi_auto_forge.config.models import AgentRole
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution


class PlanningOutput(BaseModel):
    """Structured output for planning tasks."""

    plan: str = Field(..., description="Detailed development plan")
    approach: str = Field(..., description="Recommended approach and methodology")
    phases: List[Dict[str, Any]] = Field(..., description="List of development phases")
    risks: List[str] = Field(
        default_factory=list, description="Identified risks and mitigation strategies"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Key assumptions made"
    )
    success_criteria: List[str] = Field(
        ..., description="Success criteria for the project"
    )
    estimated_complexity: str = Field(
        ..., description="Estimated complexity level (low/medium/high)"
    )
    recommended_technologies: List[str] = Field(
        default_factory=list, description="Recommended technology stack"
    )


class BrainstormingOutput(BaseModel):
    """Structured output for brainstorming tasks."""

    ideas: List[str] = Field(..., description="Generated creative ideas and approaches")
    alternatives: List[Dict[str, Any]] = Field(
        ..., description="Alternative solutions and approaches"
    )
    innovations: List[str] = Field(
        default_factory=list, description="Innovative features or approaches"
    )
    trade_offs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Trade-offs between different approaches"
    )
    recommendations: List[str] = Field(
        ..., description="Top recommendations based on brainstorming"
    )


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and brainstorming tasks."""

    def __init__(
        self,
        neo4j_client=None,
        logger: Optional[logging.Logger] = None,
        prompt_gateway=None,
        context_store=None,
    ):
        """Initialize the planner agent."""
        super().__init__(
            AgentRole.PLANNER, neo4j_client, logger, prompt_gateway, context_store
        )

    async def execute(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Execute planning or brainstorming task.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and context

        Returns:
            AgentResponse with planning results
        """
        task_name = task_execution.definition.name

        if task_name == "plan":
            return await self._create_plan(task_execution, inputs)
        elif task_name == "brainstorm":
            return await self._brainstorm_solutions(task_execution, inputs)
        else:
            return AgentResponse(
                success=False,
                content=f"Unknown planning task: {task_name}",
                errors=[f"Unsupported task type: {task_name}"],
            )

    async def _create_plan(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Create a detailed development plan.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements

        Returns:
            AgentResponse with planning results
        """
        requirements = inputs.get("requirements", "")
        project_context = inputs.get("context", {})

        # Create planning prompt
        prompt = f"""
        ## PROJECT REQUIREMENTS
        {requirements}

        ## PROJECT CONTEXT
        {json.dumps(project_context, indent=2)}

        ## PLANNING TASK
        Create a comprehensive development plan for this software project. Consider:
        - Technical architecture and design
        - Development phases and milestones
        - Risk assessment and mitigation
        - Success criteria and validation
        - Technology stack recommendations
        - Resource requirements and timeline

        Provide a structured plan that can guide the development process.
        """

        try:
            # Use LLM to generate structured planning output
            plan_output = await self._call_llm(
                task_type="planning",
                goal=f"Create a comprehensive development plan for: {requirements}",
                schema=PlanningOutput,
                constraints={
                    "project_context": project_context,
                    "requirements": requirements,
                    "planning_approach": "comprehensive and detailed",
                    "include_phases": True,
                    "include_risks": True,
                    "include_assumptions": True,
                    "include_success_criteria": True,
                },
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Created development plan with {len(plan_output.phases)} phases",
                confidence=0.9,
                params={"complexity": plan_output.estimated_complexity},
            )

            return AgentResponse(
                success=True,
                content=plan_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "plan",
                        "content": plan_output.model_dump_json(indent=2),
                        "metadata": {
                            "phases_count": len(plan_output.phases),
                            "complexity": plan_output.estimated_complexity,
                            "technologies_count": len(
                                plan_output.recommended_technologies
                            ),
                        },
                    }
                ],
                metadata={
                    "phases_count": len(plan_output.phases),
                    "complexity": plan_output.estimated_complexity,
                    "risks_count": len(plan_output.risks),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to create plan: {str(e)}", exc_info=True)
            return AgentResponse(
                success=False,
                content=f"Failed to create development plan: {str(e)}",
                errors=[str(e)],
            )

    async def _brainstorm_solutions(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Brainstorm creative solutions and approaches.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and constraints

        Returns:
            AgentResponse with brainstorming results
        """
        requirements = inputs.get("requirements", "")
        constraints = inputs.get("constraints", {})

        # Create brainstorming prompt
        prompt = f"""
        ## PROJECT REQUIREMENTS
        {requirements}

        ## CONSTRAINTS
        {json.dumps(constraints, indent=2)}

        ## BRAINSTORMING TASK
        Generate creative ideas and alternative approaches for this project. Consider:
        - Innovative features and capabilities
        - Alternative technical approaches
        - User experience improvements
        - Performance optimization strategies
        - Scalability and maintainability solutions

        Think outside the box and explore multiple possibilities.
        """

        try:
            # Use LLM to generate structured brainstorming output
            brainstorming_output = await self._call_llm(
                task_type="brainstorming",
                goal=f"Generate creative ideas and alternative approaches for: {requirements}",
                schema=BrainstormingOutput,
                constraints={
                    "project_requirements": requirements,
                    "constraints": constraints,
                    "brainstorming_approach": "creative and innovative",
                    "include_alternatives": True,
                    "include_innovations": True,
                    "include_trade_offs": True,
                    "include_recommendations": True,
                },
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Generated {len(brainstorming_output.ideas)} ideas and {len(brainstorming_output.alternatives)} alternatives",
                confidence=0.85,
                params={"ideas_count": len(brainstorming_output.ideas)},
            )

            return AgentResponse(
                success=True,
                content=brainstorming_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "brainstorming",
                        "content": brainstorming_output.model_dump_json(indent=2),
                        "metadata": {
                            "ideas_count": len(brainstorming_output.ideas),
                            "alternatives_count": len(
                                brainstorming_output.alternatives
                            ),
                            "innovations_count": len(brainstorming_output.innovations),
                        },
                    }
                ],
                metadata={
                    "ideas_count": len(brainstorming_output.ideas),
                    "alternatives_count": len(brainstorming_output.alternatives),
                    "recommendations_count": len(brainstorming_output.recommendations),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to brainstorm solutions: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to brainstorm solutions: {str(e)}",
                errors=[str(e)],
            )
