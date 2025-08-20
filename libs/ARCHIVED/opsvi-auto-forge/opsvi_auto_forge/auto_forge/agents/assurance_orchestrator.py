"""Assurance orchestrator for coordinating repair loops and quality gates."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from opsvi_auto_forge.agents.base_repair_agent import BaseRepairAgent, RepairRequest
from opsvi_auto_forge.config.models import Artifact, Critique, Result
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from opsvi_auto_forge.agents.critic_agent import (
        CriticAgent,
        CriticEvaluationResponse,
    )

logger = logging.getLogger(__name__)


class RepairLoopState(BaseModel):
    """State of a repair loop iteration."""

    iteration: int = Field(..., description="Current iteration number")
    max_iterations: int = Field(..., description="Maximum allowed iterations")
    artifact_id: UUID = Field(..., description="ID of artifact being repaired")
    original_artifact: Artifact = Field(..., description="Original artifact")
    current_artifact: Artifact = Field(
        ..., description="Current artifact being evaluated"
    )
    repair_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="History of repairs"
    )
    evaluation_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="History of evaluations"
    )
    passed: bool = Field(False, description="Whether the artifact passed evaluation")
    human_review_needed: bool = Field(
        False, description="Whether human review is needed"
    )


class AssuranceOrchestrator:
    """Orchestrates the repair loop between critic and repair agents."""

    def __init__(
        self,
        critic_agent: "CriticAgent",
        repair_agents: List[BaseRepairAgent],
        neo4j_client: Optional[Neo4jClient] = None,
        max_repair_loops: int = 3,
    ):
        """Initialize the assurance orchestrator."""
        self.critic_agent = critic_agent
        self.repair_agents = repair_agents
        self.neo4j_client = neo4j_client
        self.max_repair_loops = max_repair_loops
        self.orchestrator_id = uuid4()

    async def run_assurance_loop(
        self,
        artifact: Artifact,
        result: Result,
        context: Dict[str, Any],
    ) -> Tuple[Artifact, Critique, bool]:
        """
        Run the complete assurance loop: evaluate → repair → re-evaluate.

        Returns:
            Tuple of (final_artifact, final_critique, passed)
        """
        logger.info(f"Starting assurance loop for artifact {artifact.id}")

        # Initialize repair loop state
        loop_state = RepairLoopState(
            iteration=0,
            max_iterations=self.max_repair_loops,
            artifact_id=artifact.id,
            original_artifact=artifact,
            current_artifact=artifact,
        )

        try:
            # Run the repair loop
            final_artifact, final_critique, passed = await self._execute_repair_loop(
                loop_state, result, context
            )

            # Log the final outcome
            await self._log_assurance_outcome(loop_state, final_critique, passed)

            logger.info(
                f"Assurance loop completed for artifact {artifact.id}: "
                f"passed={passed}, iterations={loop_state.iteration}"
            )

            return final_artifact, final_critique, passed

        except Exception as e:
            logger.error(f"Error in assurance loop: {e}", exc_info=True)
            # Return original artifact with failure critique
            failure_critique = Critique(
                id=uuid4(),
                passed=False,
                score=0.0,
                policy_scores={},
                reasons=[f"Assurance loop failed: {str(e)}"],
                patch_plan=[],
            )
            return artifact, failure_critique, False

    async def _execute_repair_loop(
        self,
        loop_state: RepairLoopState,
        result: Result,
        context: Dict[str, Any],
    ) -> Tuple[Artifact, Critique, bool]:
        """Execute the repair loop until success or max iterations."""

        while loop_state.iteration < loop_state.max_iterations:
            loop_state.iteration += 1
            logger.info(
                f"Repair loop iteration {loop_state.iteration}/{loop_state.max_iterations}"
            )

            # Evaluate current artifact
            evaluation = await self.critic_agent.evaluate_artifact(
                loop_state.current_artifact, result, context
            )
            loop_state.evaluation_history.append(evaluation)

            # Check if passed
            if evaluation.passed:
                loop_state.passed = True
                logger.info(
                    f"Artifact passed evaluation on iteration {loop_state.iteration}"
                )
                return loop_state.current_artifact, evaluation.critique, True

            # Check if repair is needed
            if not evaluation.repair_needed:
                logger.info("No repair needed, but artifact failed evaluation")
                return loop_state.current_artifact, evaluation.critique, False

            # Perform repairs
            repair_success = await self._perform_repairs(loop_state, evaluation)

            if not repair_success:
                logger.warning(f"Repair failed on iteration {loop_state.iteration}")
                # Continue to next iteration with current artifact

        # Max iterations reached
        loop_state.human_review_needed = True
        logger.warning(f"Max repair iterations ({loop_state.max_iterations}) reached")

        # Return the best artifact we have
        best_evaluation = max(
            loop_state.evaluation_history, key=lambda e: e.overall_score, default=None
        )

        if best_evaluation:
            return loop_state.current_artifact, best_evaluation.critique, False
        else:
            # Fallback to original artifact
            failure_critique = Critique(
                id=uuid4(),
                passed=False,
                score=0.0,
                policy_scores={},
                reasons=["Max repair iterations reached without improvement"],
                patch_plan=[],
            )
            return loop_state.original_artifact, failure_critique, False

    async def _perform_repairs(
        self,
        loop_state: RepairLoopState,
        evaluation: "CriticEvaluationResponse",
    ) -> bool:
        """Perform repairs based on the evaluation."""
        logger.info(f"Performing repairs for iteration {loop_state.iteration}")

        repair_success = False
        current_artifact = loop_state.current_artifact

        # Process each patch plan item
        for patch_item in evaluation.patch_plan:
            try:
                # Find appropriate repair agent
                repair_agent = self._find_repair_agent(patch_item)

                if not repair_agent:
                    logger.warning(
                        f"No repair agent found for patch item: {patch_item}"
                    )
                    continue

                # Get the capability for this action
                action = patch_item.get("action", "")
                capability = self._get_capability_for_action(action)

                # Create repair request
                repair_request = RepairRequest(
                    artifact=current_artifact,
                    issue_type=capability,  # Use the mapped capability, not the action
                    issue_description=patch_item.get("description", "Unknown issue"),
                    context=patch_item.get("context", {}),
                    patch_plan=patch_item,
                )

                # Perform repair
                repair_result = await repair_agent.repair_artifact(repair_request)

                # Log repair attempt
                repair_record = {
                    "iteration": loop_state.iteration,
                    "patch_item": patch_item,
                    "repair_agent": repair_agent.name,
                    "success": repair_result.success,
                    "confidence": repair_result.confidence,
                    "changes_made": repair_result.changes_made,
                    "error_message": repair_result.error_message,
                }
                loop_state.repair_history.append(repair_record)

                # Update current artifact if repair was successful
                if repair_result.success and repair_result.fixed_artifact:
                    current_artifact = repair_result.fixed_artifact
                    repair_success = True
                    logger.info(
                        f"Repair successful: {repair_agent.name} fixed {patch_item.get('action')}"
                    )
                else:
                    logger.warning(
                        f"Repair failed: {repair_agent.name} could not fix {patch_item.get('action')}"
                    )

            except Exception as e:
                logger.error(f"Error during repair: {e}", exc_info=True)
                repair_record = {
                    "iteration": loop_state.iteration,
                    "patch_item": patch_item,
                    "repair_agent": "unknown",
                    "success": False,
                    "confidence": 0.0,
                    "changes_made": [],
                    "error_message": str(e),
                }
                loop_state.repair_history.append(repair_record)

        # Update loop state with new artifact
        loop_state.current_artifact = current_artifact

        return repair_success

    def _find_repair_agent(
        self, patch_item: Dict[str, Any]
    ) -> Optional[BaseRepairAgent]:
        """Find the appropriate repair agent for a patch item."""
        action = patch_item.get("action", "")
        capability = self._get_capability_for_action(action)

        # Find agent that can handle this capability
        for agent in self.repair_agents:
            if agent.can_repair(capability):
                return agent

        return None

    def _get_capability_for_action(self, action: str) -> str:
        """Get the repair capability for a given action."""
        # Map actions to repair capabilities
        action_to_capability = {
            "fix_syntax_errors": "syntax_error",
            "fix_formatting": "formatting_issue",
            "fix_imports": "import_error",
            "fix_security_issues": "security_vulnerability",
            "fix_compliance": "compliance_issue",
            "fix_license": "license_violation",
            "fix_secrets": "secret_exposure",
            "fix_injection": "injection_vulnerability",
            "fix_auth": "authentication_issue",
            "fix_authorization": "authorization_issue",
            "fix_data_exposure": "data_exposure",
            # Add mappings for critic agent actions
            "improve_specification": "syntax_error",  # Use syntax fixer as fallback
            "improve_architecture": "syntax_error",  # Use syntax fixer as fallback
            "improve_test_coverage": "syntax_error",  # Use syntax fixer as fallback
            "optimize_performance": "syntax_error",  # Use syntax fixer as fallback
            "general_improvement": "syntax_error",  # Use syntax fixer as fallback
            # Add mappings for policy actions
            "fix_lint_errors": "syntax_error",
            "reduce_warnings": "formatting_issue",
            "fix_type_errors": "syntax_error",
            "fix_security_issues": "security_vulnerability",
        }

        return action_to_capability.get(action, action)

    async def _log_assurance_outcome(
        self,
        loop_state: RepairLoopState,
        final_critique: Critique,
        passed: bool,
    ) -> None:
        """Log the final outcome of the assurance loop."""
        if not self.neo4j_client:
            return

        try:
            outcome_data = {
                "orchestrator_id": str(self.orchestrator_id),
                "artifact_id": str(loop_state.artifact_id),
                "iterations": loop_state.iteration,
                "max_iterations": loop_state.max_iterations,
                "passed": passed,
                "human_review_needed": loop_state.human_review_needed,
                "final_score": final_critique.score,
                "repair_history": loop_state.repair_history,
                "evaluation_history": [
                    {
                        "iteration": i + 1,
                        "score": eval.overall_score,
                        "passed": eval.passed,
                    }
                    for i, eval in enumerate(loop_state.evaluation_history)
                ],
            }

            await self.neo4j_client.create_decision(
                decision_id=uuid4(),
                agent_id=self.orchestrator_id,
                why=f"Assurance loop outcome: {'PASSED' if passed else 'FAILED'} after {loop_state.iteration} iterations",
                params=outcome_data,
                task_id=loop_state.original_artifact.task_id,
            )

        except Exception as e:
            logger.error(f"Failed to log assurance outcome: {e}", exc_info=True)

    def get_repair_agents(self) -> List[BaseRepairAgent]:
        """Get list of available repair agents."""
        return self.repair_agents.copy()

    def add_repair_agent(self, agent: BaseRepairAgent) -> None:
        """Add a repair agent to the orchestrator."""
        self.repair_agents.append(agent)

    def get_orchestrator_id(self) -> UUID:
        """Get the orchestrator ID."""
        return self.orchestrator_id
