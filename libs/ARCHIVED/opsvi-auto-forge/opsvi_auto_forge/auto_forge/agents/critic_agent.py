"""Critic agent for evaluating artifacts and generating critiques."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from opsvi_auto_forge.agents.assurance_orchestrator import AssuranceOrchestrator
from opsvi_auto_forge.agents.base_repair_agent import BaseRepairAgent
from opsvi_auto_forge.application.orchestrator.policies import (
    PolicyManager,
    PolicyResult,
)
from opsvi_auto_forge.config.models import AgentRole, Artifact, Critique, Result
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CriticAgentConfig(BaseModel):
    """Configuration for the critic agent."""

    model: str = Field(
        default="gpt-4.1-mini", description="Model to use for critic evaluation"
    )
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Temperature for model calls"
    )
    max_tokens: int = Field(
        default=4000, gt=0, description="Maximum tokens for model calls"
    )
    overall_threshold: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Overall quality threshold"
    )
    policy_threshold: float = Field(
        default=0.90, ge=0.0, le=1.0, description="Individual policy threshold"
    )
    max_repair_loops: int = Field(
        default=3, ge=1, description="Maximum repair loops allowed"
    )


class CriticEvaluationRequest(BaseModel):
    """Request for critic evaluation."""

    artifact: Artifact
    result: Result
    context: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[CriticAgentConfig] = None


class CriticEvaluationResponse(BaseModel):
    """Response from critic evaluation."""

    critique: Critique
    policy_results: List[PolicyResult]
    overall_score: float
    passed: bool
    repair_needed: bool
    patch_plan: List[Dict[str, Any]]


class CriticAgent:
    """Agent responsible for evaluating artifacts and generating critiques."""

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        config: Optional[CriticAgentConfig] = None,
    ):
        """Initialize the critic agent."""
        self.neo4j_client = neo4j_client
        self.config = config or CriticAgentConfig()
        self.policy_manager = PolicyManager(neo4j_client=neo4j_client)
        self.agent_id = uuid4()

    async def evaluate_artifact(
        self, artifact: Artifact, result: Result, context: Dict[str, Any]
    ) -> CriticEvaluationResponse:
        """Evaluate an artifact and generate a critique."""
        logger.info(f"Starting critic evaluation for artifact {artifact.id}")

        try:
            # Run all applicable policies
            policy_results = await self.policy_manager.evaluate_artifact(
                artifact, result, context
            )

            # Calculate overall score
            overall_score, passed = await self.policy_manager.calculate_overall_score(
                policy_results
            )

            # Generate patch plan for failures
            patch_plan = self._generate_patch_plan(policy_results, artifact, result)

            # Create critique
            critique = Critique(
                id=uuid4(),
                passed=passed,
                score=overall_score,
                policy_scores={
                    result.policy_name: result.score for result in policy_results
                },
                reasons=[
                    reason
                    for result in policy_results
                    if result.reasons
                    for reason in result.reasons
                ],
                patch_plan=patch_plan,
                agent_id=self.agent_id,
                model_used=self.config.model,
            )

            # Determine if repair is needed
            repair_needed = not passed and len(patch_plan) > 0

            response = CriticEvaluationResponse(
                critique=critique,
                policy_results=policy_results,
                overall_score=overall_score,
                passed=passed,
                repair_needed=repair_needed,
                patch_plan=patch_plan,
            )

            # Log to Neo4j if available
            if self.neo4j_client:
                await self._log_critique_to_neo4j(critique, artifact.id)

            logger.info(
                f"Critic evaluation completed for artifact {artifact.id}: "
                f"score={overall_score:.3f}, passed={passed}, repair_needed={repair_needed}"
            )

            return response

        except Exception as e:
            logger.error(f"Error in critic evaluation: {e}")
            # Create a failed critique
            failed_critique = Critique(
                id=uuid4(),
                passed=False,
                score=0.0,
                policy_scores={},
                reasons=[f"Critic evaluation failed: {str(e)}"],
                patch_plan=[{"action": "retry_critic_evaluation", "reason": str(e)}],
                agent_id=self.agent_id,
                model_used=self.config.model,
            )

            return CriticEvaluationResponse(
                critique=failed_critique,
                policy_results=[],
                overall_score=0.0,
                passed=False,
                repair_needed=True,
                patch_plan=[{"action": "retry_critic_evaluation", "reason": str(e)}],
            )

    def _generate_patch_plan(
        self, policy_results: List[PolicyResult], artifact: Artifact, result: Result
    ) -> List[Dict[str, Any]]:
        """Generate a patch plan based on policy failures."""
        patch_plan = []

        for policy_result in policy_results:
            if not policy_result.passed:
                # Add policy-specific patch plan items
                patch_plan.extend(policy_result.patch_plan)

                # Add general patch plan items based on policy type
                if "spec" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "improve_specification",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )
                elif "arch" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "improve_architecture",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )
                elif "code" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "improve_code_quality",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )
                elif "test" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "improve_test_coverage",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )
                elif "security" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "fix_security_issues",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )
                elif "performance" in policy_result.policy_name.lower():
                    patch_plan.append(
                        {
                            "action": "optimize_performance",
                            "policy": policy_result.policy_name,
                            "score": policy_result.score,
                            "target_score": self.config.policy_threshold,
                            "artifact_type": artifact.type,
                        }
                    )

        # Add overall improvement actions if overall score is low
        if result.score < self.config.overall_threshold:
            patch_plan.append(
                {
                    "action": "general_improvement",
                    "current_score": result.score,
                    "target_score": self.config.overall_threshold,
                    "artifact_type": artifact.type,
                }
            )

        return patch_plan

    async def _log_critique_to_neo4j(
        self, critique: Critique, artifact_id: UUID
    ) -> None:
        """Log the critique to Neo4j for lineage tracking."""
        try:
            critique_data = {
                "id": str(critique.id),
                "task_id": str(artifact_id),  # Using artifact_id as task_id for now
                "pass": critique.passed,
                "score": critique.score,
                "policy_scores": critique.policy_scores,
                "reasons": critique.reasons,
                "patch_plan": critique.patch_plan,
                "agent_id": str(critique.agent_id),
                "model_used": critique.model_used,
                "tokens_used": critique.tokens_used,
                "latency_ms": critique.latency_ms,
            }

            await self.neo4j_client.create_critique(critique_data)
            logger.info(f"Logged critique {critique.id} to Neo4j")

        except Exception as e:
            logger.error(f"Failed to log critique to Neo4j: {e}")

    async def evaluate_batch(
        self, artifacts: List[Artifact], results: List[Result], context: Dict[str, Any]
    ) -> List[CriticEvaluationResponse]:
        """Evaluate multiple artifacts in batch."""
        logger.info(f"Starting batch critic evaluation for {len(artifacts)} artifacts")

        evaluation_tasks = []
        for artifact, result in zip(artifacts, results):
            task = self.evaluate_artifact(artifact, result, context)
            evaluation_tasks.append(task)

        # Execute evaluations in parallel
        responses = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        # Handle any exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch evaluation failed for artifact {i}: {response}")
                # Create failed response
                failed_critique = Critique(
                    id=uuid4(),
                    passed=False,
                    score=0.0,
                    policy_scores={},
                    reasons=[f"Batch evaluation failed: {str(response)}"],
                    patch_plan=[
                        {"action": "retry_batch_evaluation", "reason": str(response)}
                    ],
                    agent_id=self.agent_id,
                    model_used=self.config.model,
                )
                processed_responses.append(
                    CriticEvaluationResponse(
                        critique=failed_critique,
                        policy_results=[],
                        overall_score=0.0,
                        passed=False,
                        repair_needed=True,
                        patch_plan=[
                            {
                                "action": "retry_batch_evaluation",
                                "reason": str(response),
                            }
                        ],
                    )
                )
            else:
                processed_responses.append(response)

        logger.info(
            f"Batch critic evaluation completed: {len(processed_responses)} responses"
        )
        return processed_responses

    def get_agent_role(self) -> AgentRole:
        """Get the agent role."""
        return AgentRole.CRITIC

    def get_agent_id(self) -> UUID:
        """Get the agent ID."""
        return self.agent_id

    async def run_assurance_loop(
        self,
        artifact: Artifact,
        result: Result,
        context: Dict[str, Any],
        repair_agents: Optional[List[BaseRepairAgent]] = None,
    ) -> tuple[Artifact, Critique, bool]:
        """
        Run the complete assurance loop with repair capabilities.

        Args:
            artifact: The artifact to evaluate and potentially repair
            result: The result associated with the artifact
            context: Additional context for evaluation
            repair_agents: List of repair agents to use (optional)

        Returns:
            Tuple of (final_artifact, final_critique, passed)
        """
        logger.info(f"Starting assurance loop for artifact {artifact.id}")

        # Get repair agents if not provided
        if repair_agents is None:
            from opsvi_auto_forge.agents import agent_registry

            repair_agents = agent_registry.get_all_repair_agents(
                neo4j_client=self.neo4j_client
            )

        # Create assurance orchestrator
        orchestrator = AssuranceOrchestrator(
            critic_agent=self,
            repair_agents=repair_agents,
            neo4j_client=self.neo4j_client,
            max_repair_loops=self.config.max_repair_loops,
        )

        # Run the assurance loop
        return await orchestrator.run_assurance_loop(artifact, result, context)
