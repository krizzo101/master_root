"""
Workflow Context Management

Manages state, context, and data flow between workflow steps in autonomous execution mode.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class WorkflowContext:
    """
    Central context manager for autonomous workflow execution.

    Tracks the complete workflow state, manages context between steps,
    and provides intelligent context filtering for each step.
    """

    # Define SDLC step dependencies - pure software development workflow


STEP_DEPENDENCIES = {
    "requirements-analyze": [],  # Starting point: problem statement -> requirements
    "system-design": [
        "requirements-analyze"
    ],  # High-level architecture from requirements
    "tech-spec-generate": ["requirements-analyze", "system-design"],  # Detailed specs
    "api-spec-generate": [
        "tech-spec-generate",
        "system-design",
    ],  # API design from specs
    "database-generate": [
        "tech-spec-generate",
        "api-spec-generate",
    ],  # Schema from API needs
    "component-design": [
        "system-design",
        "tech-spec-generate",
        "api-spec-generate",
    ],  # Components from architecture
    "interface-design": [
        "component-design",
        "api-spec-generate",
        "requirements-analyze",
    ],  # UI from components and requirements
    "implementation-plan": [
        "component-design",
        "interface-design",
        "database-generate",
    ],  # Dev roadmap from all designs
    "testing-strategy": [
        "implementation-plan",
        "requirements-analyze",
    ],  # Test plans from implementation and requirements
}


class WorkflowContext:
    """Central context manager for autonomous workflow execution."""

    # Define SDLC step dependencies - pure software development workflow
    STEP_DEPENDENCIES = STEP_DEPENDENCIES

    def __init__(self, initial_problem: str, workflow_id: Optional[str] = None):
        """
        Initialize workflow context.

        Args:
            initial_problem: The original problem statement driving the workflow
            workflow_id: Optional workflow ID for resuming existing workflows
        """
        self.workflow_id = workflow_id or str(uuid.uuid4())[:8]
        self.initial_problem = initial_problem
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Workflow state
        self.steps_completed: List[str] = []
        self.current_step: Optional[str] = None
        self.step_outputs: Dict[str, Any] = {}
        self.step_metadata: Dict[str, Dict[str, Any]] = {}

        # Key selections and derived data
        self.selected_idea: Optional[Dict[str, Any]] = None
        self.idea_selection_rationale: Optional[str] = None

        # File tracking
        self.output_directory: Optional[Path] = None
        self.step_files: Dict[str, List[str]] = {}

        # Workflow configuration
        self.enabled_steps: List[str] = list(self.STEP_DEPENDENCIES.keys())
        self.step_config: Dict[str, Dict[str, Any]] = {}

    def add_step_output(
        self, step_name: str, output: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add output from a completed workflow step.

        Args:
            step_name: Name of the completed step
            output: The primary output from the step
            metadata: Optional metadata about the step execution
        """
        self.step_outputs[step_name] = output
        self.step_metadata[step_name] = metadata or {}

        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)

        self.updated_at = datetime.now()

        # Auto-select best idea after idea-analyze step
        if step_name == "idea-analyze" and "selected_idea" in output:
            self.selected_idea = output["selected_idea"]
            self.idea_selection_rationale = output.get("selection_rationale", "")

    def get_step_output(self, step_name: str) -> Optional[Any]:
        """Get output from a specific step."""
        return self.step_outputs.get(step_name)

    def get_relevant_context_for_step(self, step_name: str) -> Dict[str, Any]:
        """
        Get relevant context for a specific workflow step.

        Args:
            step_name: Name of the step that needs context

        Returns:
            Dictionary containing relevant context from previous steps
        """
        context = {
            "initial_problem": self.initial_problem,
            "workflow_id": self.workflow_id,
            "selected_idea": self.selected_idea,
        }

        # Add outputs from dependency steps
        dependencies = self.STEP_DEPENDENCIES.get(step_name, [])
        for dep_step in dependencies:
            if dep_step in self.step_outputs:
                context[dep_step] = self.step_outputs[dep_step]

        # Add step-specific context enhancement
        context.update(self._get_enhanced_context_for_step(step_name))

        return context

    def _get_enhanced_context_for_step(self, step_name: str) -> Dict[str, Any]:
        """
        Get enhanced context specific to each step type.

        This method provides step-specific context that goes beyond
        the basic dependency outputs.
        """
        enhanced_context = {}

        if step_name == "requirements-analyze":
            # Requirements need comprehensive context from all analysis steps
            enhanced_context.update(
                {
                    "problem_analysis": self._synthesize_problem_analysis(),
                    "market_insights": self._extract_market_insights(),
                    "feasibility_constraints": self._extract_feasibility_constraints(),
                }
            )

        elif step_name in ["api-spec-generate", "database-generate"]:
            # Technical specs need structured requirements and technical context
            enhanced_context.update(
                {
                    "technical_requirements": self._extract_technical_requirements(),
                    "functional_requirements": self._extract_functional_requirements(),
                    "non_functional_requirements": self._extract_non_functional_requirements(),
                }
            )

        elif step_name in ["architecture-design", "component-design"]:
            # Architecture steps need all technical specifications
            enhanced_context.update(
                {
                    "api_overview": self._extract_api_overview(),
                    "data_model": self._extract_data_model(),
                    "integration_requirements": self._extract_integration_requirements(),
                }
            )

        return enhanced_context

    def _synthesize_problem_analysis(self) -> Dict[str, Any]:
        """Synthesize problem analysis from completed steps."""
        analysis = {"core_problem": self.initial_problem}

        if self.selected_idea:
            analysis["selected_solution"] = {
                "title": self.selected_idea.get("title", ""),
                "description": self.selected_idea.get("description", ""),
                "category": self.selected_idea.get("category", ""),
            }

        if "market-research" in self.step_outputs:
            market_data = self.step_outputs["market-research"]
            analysis["market_context"] = {
                "target_audience": market_data.get("target_audience", ""),
                "market_size": market_data.get("market_size", ""),
                "competitors": market_data.get("competitors", []),
            }

        return analysis

    def _extract_market_insights(self) -> Dict[str, Any]:
        """Extract key market insights for requirements analysis."""
        if "market-research" not in self.step_outputs:
            return {}

        market_data = self.step_outputs["market-research"]
        return {
            "opportunities": market_data.get("opportunities", []),
            "threats": market_data.get("threats", []),
            "user_needs": market_data.get("user_needs", []),
            "success_factors": market_data.get("success_factors", []),
        }

    def _extract_feasibility_constraints(self) -> Dict[str, Any]:
        """Extract feasibility constraints and considerations."""
        if "feasibility-assess" not in self.step_outputs:
            return {}

        feasibility_data = self.step_outputs["feasibility-assess"]
        return {
            "technical_constraints": feasibility_data.get("technical_constraints", []),
            "resource_constraints": feasibility_data.get("resource_constraints", []),
            "risk_factors": feasibility_data.get("risk_factors", []),
            "implementation_complexity": feasibility_data.get(
                "complexity_score", "Medium"
            ),
        }

    def _extract_technical_requirements(self) -> Dict[str, Any]:
        """Extract technical requirements for API and database design."""
        if "requirements-analyze" not in self.step_outputs:
            return {}

        req_data = self.step_outputs["requirements-analyze"]
        return {
            "technical_requirements": req_data.get("technical_requirements", []),
            "performance_requirements": req_data.get("performance_requirements", []),
            "security_requirements": req_data.get("security_requirements", []),
            "scalability_requirements": req_data.get("scalability_requirements", []),
        }

    def _extract_functional_requirements(self) -> Dict[str, Any]:
        """Extract functional requirements."""
        if "requirements-analyze" not in self.step_outputs:
            return {}

        req_data = self.step_outputs["requirements-analyze"]
        return {
            "functional_requirements": req_data.get("functional_requirements", []),
            "user_stories": req_data.get("user_stories", []),
            "use_cases": req_data.get("use_cases", []),
        }

    def _extract_non_functional_requirements(self) -> Dict[str, Any]:
        """Extract non-functional requirements."""
        if "requirements-analyze" not in self.step_outputs:
            return {}

        req_data = self.step_outputs["requirements-analyze"]
        return {
            "performance": req_data.get("performance_requirements", []),
            "security": req_data.get("security_requirements", []),
            "usability": req_data.get("usability_requirements", []),
            "reliability": req_data.get("reliability_requirements", []),
        }

    def _extract_api_overview(self) -> Dict[str, Any]:
        """Extract API overview for architecture design."""
        if "api-spec-generate" not in self.step_outputs:
            return {}

        api_data = self.step_outputs["api-spec-generate"]
        return {
            "endpoints": api_data.get("endpoints", []),
            "authentication": api_data.get("authentication", {}),
            "data_models": api_data.get("models", []),
        }

    def _extract_data_model(self) -> Dict[str, Any]:
        """Extract data model for architecture design."""
        if "database-generate" not in self.step_outputs:
            return {}

        db_data = self.step_outputs["database-generate"]
        return {
            "tables": db_data.get("tables", []),
            "relationships": db_data.get("relationships", []),
            "indexes": db_data.get("indexes", []),
        }

    def _extract_integration_requirements(self) -> Dict[str, Any]:
        """Extract integration requirements."""
        if "integration-spec-generate" not in self.step_outputs:
            return {}

        integration_data = self.step_outputs["integration-spec-generate"]
        return {
            "external_apis": integration_data.get("external_apis", []),
            "data_flows": integration_data.get("data_flows", []),
            "communication_patterns": integration_data.get(
                "communication_patterns", []
            ),
        }

    def is_step_ready(self, step_name: str) -> bool:
        """
        Check if a step is ready to execute (all dependencies completed).

        Args:
            step_name: Name of the step to check

        Returns:
            True if all dependencies are completed
        """
        dependencies = self.STEP_DEPENDENCIES.get(step_name, [])
        return all(dep in self.steps_completed for dep in dependencies)

    def get_next_ready_steps(self) -> List[str]:
        """Get list of steps that are ready to execute."""
        ready_steps = []
        for step in self.enabled_steps:
            if step not in self.steps_completed and self.is_step_ready(step):
                ready_steps.append(step)
        return ready_steps

    def get_workflow_progress(self) -> Dict[str, Any]:
        """Get workflow progress summary."""
        total_steps = len(self.enabled_steps)
        completed_steps = len(self.steps_completed)

        return {
            "workflow_id": self.workflow_id,
            "progress_percent": (
                (completed_steps / total_steps * 100) if total_steps > 0 else 0
            ),
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "next_steps": self.get_next_ready_steps(),
        }

    def set_output_directory(self, base_path: Path) -> Path:
        """Set and create the output directory for this workflow."""
        timestamp = self.created_at.strftime("%Y%m%d_%H%M%S")
        self.output_directory = base_path / f"workflow_{self.workflow_id}_{timestamp}"
        self.output_directory.mkdir(parents=True, exist_ok=True)
        return self.output_directory

    def get_step_output_directory(self, step_name: str) -> Path:
        """Get output directory for a specific step."""
        if not self.output_directory:
            raise ValueError(
                "Output directory not set. Call set_output_directory() first."
            )

        step_order = (
            list(self.STEP_DEPENDENCIES.keys()).index(step_name)
            if step_name in self.STEP_DEPENDENCIES
            else 99
        )
        step_dir = self.output_directory / f"{step_order:02d}_{step_name}"
        step_dir.mkdir(exist_ok=True)
        return step_dir

    def save_context(self) -> Path:
        """Save workflow context to file."""
        if not self.output_directory:
            raise ValueError(
                "Output directory not set. Call set_output_directory() first."
            )

        context_file = self.output_directory / "workflow_context.json"
        context_data = {
            "workflow_id": self.workflow_id,
            "initial_problem": self.initial_problem,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "steps_completed": self.steps_completed,
            "current_step": self.current_step,
            "selected_idea": self.selected_idea,
            "idea_selection_rationale": self.idea_selection_rationale,
            "enabled_steps": self.enabled_steps,
            "step_outputs": self.step_outputs,
            "step_metadata": self.step_metadata,
            "progress": self.get_workflow_progress(),
        }

        with open(context_file, "w") as f:
            json.dump(context_data, f, indent=2, default=str)

        return context_file

    @classmethod
    def load_context(cls, context_file: Path) -> "WorkflowContext":
        """Load workflow context from file."""
        with open(context_file, "r") as f:
            data = json.load(f)

        context = cls(
            initial_problem=data["initial_problem"], workflow_id=data["workflow_id"]
        )

        context.created_at = datetime.fromisoformat(data["created_at"])
        context.updated_at = datetime.fromisoformat(data["updated_at"])
        context.steps_completed = data["steps_completed"]
        context.current_step = data["current_step"]
        context.selected_idea = data["selected_idea"]
        context.idea_selection_rationale = data["idea_selection_rationale"]
        context.enabled_steps = data["enabled_steps"]
        context.step_outputs = data["step_outputs"]
        context.step_metadata = data["step_metadata"]

        # Set output directory based on context file location
        context.output_directory = context_file.parent

        return context
