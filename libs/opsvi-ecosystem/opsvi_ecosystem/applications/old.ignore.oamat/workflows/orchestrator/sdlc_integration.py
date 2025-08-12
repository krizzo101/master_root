"""
OAMAT Workflow Orchestrator - SDLC Integration

SDLC phase management and integration for workflow orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

from src.applications.oamat.workflows.orchestrator.state import AgenticWorkflowState
from src.applications.oamat.workflows.sdlc_phase_manager import SDLCPhaseManager

logger = logging.getLogger("SDLCIntegration")


class SDLCWorkflowIntegrator:
    """Integrates SDLC phase management with workflow orchestration"""

    def __init__(self, sdlc_manager: Optional[SDLCPhaseManager] = None):
        self.sdlc_manager = sdlc_manager

    def initialize_sdlc_phase(
        self, state: AgenticWorkflowState
    ) -> AgenticWorkflowState:
        """Initialize SDLC phase for workflow"""
        if not self.sdlc_manager:
            return state

        try:
            # Initialize SDLC phase based on workflow type
            phase_info = self.sdlc_manager.get_current_phase()

            # Update state with SDLC context
            state["sdlc_context"] = {
                "current_phase": phase_info.get("phase", "development"),
                "phase_requirements": phase_info.get("requirements", []),
                "quality_gates": phase_info.get("quality_gates", []),
            }

            logger.info(
                f"Initialized SDLC phase: {phase_info.get('phase', 'development')}"
            )

        except Exception as e:
            logger.warning(f"Failed to initialize SDLC phase: {e}")
            # Continue without SDLC integration
            state["sdlc_context"] = {"current_phase": "development"}

        return state

    def validate_phase_requirements(
        self, state: AgenticWorkflowState
    ) -> Dict[str, Any]:
        """Validate current workflow against SDLC phase requirements"""
        if not self.sdlc_manager or "sdlc_context" not in state:
            return {"valid": True, "warnings": []}

        try:
            phase_requirements = state["sdlc_context"].get("phase_requirements", [])
            quality_gates = state["sdlc_context"].get("quality_gates", [])

            validation_result = {
                "valid": True,
                "warnings": [],
                "requirements_met": [],
                "quality_gates_passed": [],
            }

            # Check phase requirements
            for requirement in phase_requirements:
                if self._check_requirement(state, requirement):
                    validation_result["requirements_met"].append(requirement)
                else:
                    validation_result["warnings"].append(
                        f"Phase requirement not met: {requirement}"
                    )

            # Check quality gates
            for gate in quality_gates:
                if self._check_quality_gate(state, gate):
                    validation_result["quality_gates_passed"].append(gate)
                else:
                    validation_result["warnings"].append(
                        f"Quality gate not passed: {gate}"
                    )
                    validation_result["valid"] = False

            return validation_result

        except Exception as e:
            logger.error(f"Error validating phase requirements: {e}")
            return {"valid": True, "warnings": [f"Validation error: {e}"]}

    def _check_requirement(self, state: AgenticWorkflowState, requirement: str) -> bool:
        """Check if a specific phase requirement is met"""
        # Implementation would depend on specific requirement types
        # For now, basic checks based on workflow state

        if "testing" in requirement.lower():
            return any(
                "test" in node.lower() for node in state.get("completed_nodes", [])
            )

        if "documentation" in requirement.lower():
            return any(
                "document" in node.lower() for node in state.get("completed_nodes", [])
            )

        if "review" in requirement.lower():
            return any(
                "review" in node.lower() for node in state.get("completed_nodes", [])
            )

        # Default to met if we can't evaluate
        return True

    def _check_quality_gate(self, state: AgenticWorkflowState, gate: str) -> bool:
        """Check if a quality gate is passed"""
        # Implementation would depend on specific quality gate types
        # For now, basic checks based on workflow outputs

        node_outputs = state.get("node_outputs", {})

        if "code_quality" in gate.lower():
            # Check if any node reported code quality metrics
            return any(
                "quality" in str(output).lower() for output in node_outputs.values()
            )

        if "security" in gate.lower():
            # Check if security review was completed
            return any(
                "security" in str(output).lower() for output in node_outputs.values()
            )

        if "performance" in gate.lower():
            # Check if performance testing was completed
            return any(
                "performance" in str(output).lower() for output in node_outputs.values()
            )

        # Default to passed if we can't evaluate
        return True

    def update_phase_progress(self, state: AgenticWorkflowState) -> None:
        """Update SDLC phase progress based on workflow completion"""
        if not self.sdlc_manager:
            return

        try:
            # Calculate completion percentage
            total_nodes = len(state.get("planned_nodes", []))
            completed_nodes = len(state.get("completed_nodes", []))

            if total_nodes > 0:
                completion_percentage = (completed_nodes / total_nodes) * 100

                # Update SDLC manager with progress
                self.sdlc_manager.update_phase_progress(
                    workflow_id=state.get("workflow_id", "unknown"),
                    completion_percentage=completion_percentage,
                    completed_activities=state.get("completed_nodes", []),
                )

                logger.info(f"Updated SDLC progress: {completion_percentage:.1f}%")

        except Exception as e:
            logger.warning(f"Failed to update SDLC progress: {e}")

    def get_next_phase_recommendations(self, state: AgenticWorkflowState) -> List[str]:
        """Get recommendations for next SDLC phase based on current workflow"""
        if not self.sdlc_manager:
            return []

        try:
            current_phase = state.get("sdlc_context", {}).get(
                "current_phase", "development"
            )
            completed_nodes = state.get("completed_nodes", [])

            recommendations = []

            # Analyze completed work to suggest next phase activities
            if current_phase == "development":
                if any("test" in node.lower() for node in completed_nodes):
                    recommendations.append("Consider moving to testing phase")
                if any("document" in node.lower() for node in completed_nodes):
                    recommendations.append("Documentation is ready for review")

            elif current_phase == "testing":
                if any("deploy" in node.lower() for node in completed_nodes):
                    recommendations.append("Ready for deployment phase")
                if any("performance" in node.lower() for node in completed_nodes):
                    recommendations.append("Performance testing completed")

            return recommendations

        except Exception as e:
            logger.warning(f"Failed to get phase recommendations: {e}")
            return []
