"""
SDLC Phase Manager for OAMAT

This module provides sophisticated workflow pattern enforcement with configurable
phases, artifact management, and context injection for multi-agent workflows.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("SDLCPhaseManager")


class PhaseStatus(Enum):
    """Phase execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseArtifact:
    """Represents a required phase artifact"""

    path: str
    description: str
    template: str | None = None
    type: str = "file"  # file or directory
    required: bool = True


@dataclass
class PhaseValidation:
    """Validation rule for phase completion"""

    rule: str
    artifacts: list[str] | None = None
    min_chars: int | None = None
    path: str | None = None
    check: str | None = None


@dataclass
class WorkflowPhase:
    """Represents a single phase in the workflow"""

    name: str
    description: str
    order: int
    required: bool
    agents: list[str]
    depends_on: list[str] = field(default_factory=list)
    context_from: list[str] = field(default_factory=list)
    required_artifacts: list[PhaseArtifact] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    validation: list[PhaseValidation] = field(default_factory=list)
    estimated_duration: str | None = None
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: datetime | None = None
    completion_time: datetime | None = None
    context_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPattern:
    """Complete workflow pattern definition"""

    name: str
    description: str
    version: str
    applies_to: list[str]
    phases: dict[str, WorkflowPhase]
    settings: dict[str, Any]
    template_directory: str | None = None
    prompt_enhancements: dict[str, bool] = field(default_factory=dict)


class SDLCPhaseManager:
    """
    Manages SDLC workflow patterns with phase enforcement, artifact management,
    and context injection for multi-agent workflows.
    """

    def __init__(self, project_path: str, config_dir: str = None):
        self.project_path = Path(project_path)
        self.config_dir = (
            Path(config_dir)
            if config_dir
            else Path("src/applications/oamat/config/workflow_patterns")
        )
        self.current_pattern: WorkflowPattern | None = None
        self.phase_execution_log: list[dict[str, Any]] = []

        # Ensure project phases directory exists
        self.phases_dir = self.project_path / "phases"
        self.phases_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SDLC Phase Manager initialized for project: {self.project_path}")

    async def initialize_project(
        self, project_name: str, user_request: str, context: dict[str, Any] = None
    ):
        """
        Initializes a new project directory and sets up the workflow.
        """
        # Form the full path to the new project directory
        project_path = Path(self.project_path) / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Update the manager's project path to the newly created project
        self.project_path = project_path

        # Ensure the phases subdirectory exists within the new project path
        self.phases_dir = self.project_path / "phases"
        self.phases_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Project directory created at: {self.project_path}")

        # Initialize the workflow, which loads the pattern and creates artifact directories
        self.initialize_workflow(user_request, context)
        logger.info(f"Initialized project '{project_name}' for SDLC workflow.")

    def detect_workflow_type(
        self, user_request: str, context: dict[str, Any] = None
    ) -> str:
        """
        Automatically detect workflow type based on user request and context.

        Args:
            user_request: The user's request text
            context: Additional context information

        Returns:
            Detected workflow pattern name
        """
        request_lower = user_request.lower()

        # Load available patterns and check which one applies
        available_patterns = self.list_available_patterns()

        for pattern_file in available_patterns:
            pattern = self.load_workflow_pattern(pattern_file)
            if pattern and pattern.applies_to:
                for applies_to_term in pattern.applies_to:
                    if applies_to_term.lower() in request_lower:
                        logger.info(
                            f"Detected workflow type: {pattern.name} (matched: {applies_to_term})"
                        )
                        return pattern.name

        # Default to software development if no specific match
        logger.info("No specific workflow detected, defaulting to software_development")
        return "software_development"

    def list_available_patterns(self) -> list[str]:
        """List all available workflow pattern files"""
        if not self.config_dir.exists():
            logger.warning(f"Workflow patterns directory not found: {self.config_dir}")
            return []

        pattern_files = []
        for file_path in self.config_dir.glob("*.yml"):
            pattern_files.append(file_path.stem)

        return pattern_files

    def load_workflow_pattern(self, pattern_name: str) -> WorkflowPattern | None:
        """
        Load a workflow pattern from configuration file.

        Args:
            pattern_name: Name of the pattern to load

        Returns:
            Loaded WorkflowPattern or None if not found
        """
        pattern_file = self.config_dir / f"{pattern_name}.yml"

        if not pattern_file.exists():
            logger.error(f"Workflow pattern file not found: {pattern_file}")
            return None

        try:
            with open(pattern_file, encoding="utf-8") as f:
                pattern_data = yaml.safe_load(f)

            # Parse phases
            phases = {}
            for phase_id, phase_data in pattern_data.get("phases", {}).items():
                # Parse artifacts
                artifacts = []
                for artifact_data in phase_data.get("required_artifacts", []):
                    artifact = PhaseArtifact(
                        path=artifact_data["path"],
                        description=artifact_data["description"],
                        template=artifact_data.get("template"),
                        type=artifact_data.get("type", "file"),
                    )
                    artifacts.append(artifact)

                # Parse validation rules
                validations = []
                for val_data in phase_data.get("validation", []):
                    validation = PhaseValidation(
                        rule=val_data["rule"],
                        artifacts=val_data.get("artifacts"),
                        min_chars=val_data.get("min_chars"),
                        path=val_data.get("path"),
                        check=val_data.get("check"),
                    )
                    validations.append(validation)

                phase = WorkflowPhase(
                    name=phase_data["name"],
                    description=phase_data["description"],
                    order=phase_data["order"],
                    required=phase_data["required"],
                    agents=phase_data["agents"],
                    depends_on=phase_data.get("depends_on", []),
                    context_from=phase_data.get("context_from", []),
                    required_artifacts=artifacts,
                    success_criteria=phase_data.get("success_criteria", []),
                    validation=validations,
                    estimated_duration=phase_data.get("estimated_duration"),
                )
                phases[phase_id] = phase

            pattern = WorkflowPattern(
                name=pattern_data["name"],
                description=pattern_data["description"],
                version=pattern_data["version"],
                applies_to=pattern_data.get("applies_to", []),
                phases=phases,
                settings=pattern_data.get("settings", {}),
                template_directory=pattern_data.get("template_directory"),
                prompt_enhancements=pattern_data.get("prompt_enhancements", {}),
            )

            logger.info(f"Successfully loaded workflow pattern: {pattern.name}")
            return pattern

        except Exception as e:
            logger.error(f"Error loading workflow pattern {pattern_name}: {e}")
            return None

    def initialize_workflow(
        self, user_request: str, context: dict[str, Any] = None
    ) -> bool:
        """
        Initialize workflow based on detected pattern.

        Args:
            user_request: The user's request
            context: Additional context

        Returns:
            True if workflow initialized successfully
        """
        workflow_type = self.detect_workflow_type(user_request, context)
        pattern = self.load_workflow_pattern(workflow_type)

        if not pattern:
            logger.error(f"Failed to load workflow pattern: {workflow_type}")
            return False

        self.current_pattern = pattern

        # Create phase directories
        for phase_id, phase in pattern.phases.items():
            for artifact in phase.required_artifacts:
                artifact_path = self.project_path / artifact.path
                if artifact.type == "directory":
                    artifact_path.mkdir(parents=True, exist_ok=True)
                else:
                    artifact_path.parent.mkdir(parents=True, exist_ok=True)

        # Log workflow initialization
        self.phase_execution_log.append(
            {
                "action": "workflow_initialized",
                "pattern": pattern.name,
                "timestamp": datetime.now().isoformat(),
                "user_request": user_request,
            }
        )

        logger.info(f"Workflow initialized with pattern: {pattern.name}")
        return True

    def get_next_phase(self) -> str | None:
        """
        Get the next phase that should be executed based on dependencies and current status.

        Returns:
            Phase ID of next phase to execute, or None if workflow is complete
        """
        if not self.current_pattern:
            return None

        # Get phases sorted by order
        sorted_phases = sorted(
            self.current_pattern.phases.items(), key=lambda x: x[1].order
        )

        for phase_id, phase in sorted_phases:
            if phase.status == PhaseStatus.PENDING:
                # Check if dependencies are satisfied
                if self._are_dependencies_satisfied(phase_id):
                    return phase_id

        return None

    def _are_dependencies_satisfied(self, phase_id: str) -> bool:
        """Check if all dependencies for a phase are satisfied"""
        if not self.current_pattern:
            return False

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            return False

        for dep_phase_id in phase.depends_on:
            dep_phase = self.current_pattern.phases.get(dep_phase_id)
            if not dep_phase or dep_phase.status != PhaseStatus.COMPLETED:
                return False

        return True

    def start_phase(self, phase_id: str) -> bool:
        """
        Mark a phase as started and prepare its context.

        Args:
            phase_id: ID of the phase to start

        Returns:
            True if phase started successfully
        """
        if not self.current_pattern:
            logger.error("No workflow pattern loaded")
            return False

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            logger.error(f"Phase not found: {phase_id}")
            return False

        if not self._are_dependencies_satisfied(phase_id):
            logger.error(f"Dependencies not satisfied for phase: {phase_id}")
            return False

        phase.status = PhaseStatus.IN_PROGRESS
        phase.start_time = datetime.now()

        # Build context from previous phases
        phase.context_data = self._build_phase_context(phase_id)

        # Log phase start
        self.phase_execution_log.append(
            {
                "action": "phase_started",
                "phase_id": phase_id,
                "phase_name": phase.name,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"Started phase: {phase.name} ({phase_id})")
        return True

    def _build_phase_context(self, phase_id: str) -> dict[str, Any]:
        """Build context data for a phase from previous phases"""
        if not self.current_pattern:
            return {}

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            return {}

        context = {
            "phase_name": phase.name,
            "phase_description": phase.description,
            "success_criteria": phase.success_criteria,
            "required_artifacts": [a.path for a in phase.required_artifacts],
            "previous_phases": {},
        }

        # Load artifacts from previous phases that this phase depends on
        for context_phase_id in phase.context_from:
            context_phase = self.current_pattern.phases.get(context_phase_id)
            if context_phase and context_phase.status == PhaseStatus.COMPLETED:
                phase_artifacts = {}

                for artifact in context_phase.required_artifacts:
                    artifact_path = self.project_path / artifact.path
                    if artifact_path.exists() and artifact.type == "file":
                        try:
                            with open(artifact_path, encoding="utf-8") as f:
                                content = f.read()
                                if len(content) <= 5000:  # Only include smaller files
                                    phase_artifacts[artifact_path.name] = content
                                else:
                                    phase_artifacts[
                                        artifact_path.name
                                    ] = f"[Large file - {len(content)} chars]"
                        except Exception as e:
                            logger.warning(
                                f"Could not read artifact {artifact_path}: {e}"
                            )

                context["previous_phases"][context_phase_id] = {
                    "name": context_phase.name,
                    "artifacts": phase_artifacts,
                }

        return context

    async def complete_phase(
        self, phase_id: str, result: dict[str, Any] = None
    ) -> bool:
        """
        Mark a phase as completed after validating artifacts.

        Args:
            phase_id: ID of the phase to complete
            result: The result from the agent execution for this phase (optional)

        Returns:
            True if phase completed successfully
        """
        if not self.current_pattern:
            logger.error("No workflow pattern loaded")
            return False

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            logger.error(f"Phase not found: {phase_id}")
            return False

        # Validate phase completion
        validation_result = self.validate_phase(phase_id)
        if not validation_result["valid"]:
            logger.error(f"Phase validation failed: {validation_result['errors']}")
            phase.status = PhaseStatus.FAILED
            return False

        phase.status = PhaseStatus.COMPLETED
        phase.completion_time = datetime.now()

        # Log phase completion
        self.phase_execution_log.append(
            {
                "action": "phase_completed",
                "phase_id": phase_id,
                "phase_name": phase.name,
                "timestamp": datetime.now().isoformat(),
                "validation_result": validation_result,
                "agent_result": result,
            }
        )

        logger.info(f"Completed phase: {phase.name} ({phase_id})")
        return True

    def validate_phase(self, phase_id: str) -> dict[str, Any]:
        """
        Validate that a phase has been completed successfully.

        Args:
            phase_id: ID of the phase to validate

        Returns:
            Validation result with status and any errors
        """
        if not self.current_pattern:
            return {"valid": False, "errors": ["No workflow pattern loaded"]}

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            return {"valid": False, "errors": [f"Phase not found: {phase_id}"]}

        errors = []

        # Check required artifacts exist
        for artifact in phase.required_artifacts:
            artifact_path = self.project_path / artifact.path

            if artifact.type == "directory":
                if not artifact_path.exists() or not artifact_path.is_dir():
                    errors.append(f"Required directory missing: {artifact.path}")
            else:
                if not artifact_path.exists() or not artifact_path.is_file():
                    errors.append(f"Required file missing: {artifact.path}")

        # Apply validation rules
        for validation in phase.validation:
            if validation.rule == "artifacts_exist":
                for artifact_name in validation.artifacts or []:
                    # Find artifact by name in phase artifacts
                    found = False
                    for artifact in phase.required_artifacts:
                        if Path(artifact.path).name == artifact_name:
                            artifact_path = self.project_path / artifact.path
                            if artifact_path.exists():
                                found = True
                                break
                    if not found:
                        errors.append(
                            f"Validation failed: artifact {artifact_name} not found"
                        )

            elif validation.rule == "min_content_length":
                for artifact_name in validation.artifacts or []:
                    for artifact in phase.required_artifacts:
                        if Path(artifact.path).name == artifact_name:
                            artifact_path = self.project_path / artifact.path
                            if artifact_path.exists():
                                try:
                                    with open(artifact_path, encoding="utf-8") as f:
                                        content = f.read()
                                        if len(content) < (validation.min_chars or 0):
                                            errors.append(
                                                f"Validation failed: {artifact_name} too short ({len(content)} < {validation.min_chars} chars)"
                                            )
                                except Exception as e:
                                    errors.append(
                                        f"Validation failed: could not read {artifact_name}: {e}"
                                    )

            elif validation.rule == "directory_exists":
                if validation.path:
                    dir_path = self.project_path / validation.path
                    if not dir_path.exists() or not dir_path.is_dir():
                        errors.append(
                            f"Validation failed: directory {validation.path} not found"
                        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "phase_id": phase_id,
            "phase_name": phase.name,
        }

    def get_phase_context(self, phase_id: str) -> dict[str, Any]:
        """Get context data for a specific phase"""
        if not self.current_pattern:
            return {}

        phase = self.current_pattern.phases.get(phase_id)
        if not phase:
            return {}

        return phase.context_data

    def find_phase_for_agent(self, agent_role: str) -> str | None:
        """Finds the phase_id for a given agent_role."""
        if not self.current_pattern:
            return None
        for phase_id, phase in self.current_pattern.phases.items():
            if agent_role in phase.agents:
                return phase_id
        logger.warning(f"No phase found for agent role: {agent_role}")
        return None

    def get_workflow_status(self) -> dict[str, Any]:
        """Get overall workflow status"""
        if not self.current_pattern:
            return {"status": "no_workflow", "message": "No workflow pattern loaded"}

        total_phases = len(self.current_pattern.phases)
        completed_phases = sum(
            1
            for p in self.current_pattern.phases.values()
            if p.status == PhaseStatus.COMPLETED
        )
        failed_phases = sum(
            1
            for p in self.current_pattern.phases.values()
            if p.status == PhaseStatus.FAILED
        )

        if failed_phases > 0:
            status = "failed"
        elif completed_phases == total_phases:
            status = "completed"
        elif completed_phases > 0:
            status = "in_progress"
        else:
            status = "pending"

        return {
            "status": status,
            "pattern_name": self.current_pattern.name,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": failed_phases,
            "progress_percentage": (completed_phases / total_phases) * 100
            if total_phases > 0
            else 0,
            "current_phase": self.get_next_phase(),
            "execution_log": self.phase_execution_log,
        }

    def get_enhanced_agent_prompt(
        self, agent_role: str, base_prompt: str, current_phase_id: str = None
    ) -> str:
        """
        Enhance agent prompt with phase context and requirements.

        Args:
            agent_role: Role of the agent
            base_prompt: Base prompt for the agent
            current_phase_id: Current phase being executed

        Returns:
            Enhanced prompt with phase context
        """
        if not self.current_pattern or not current_phase_id:
            return base_prompt

        phase = self.current_pattern.phases.get(current_phase_id)
        if not phase:
            return base_prompt

        # Build phase-specific enhancement
        enhancement = f"""
## 📋 SDLC PHASE CONTEXT

**Current Phase**: {phase.name}
**Phase Description**: {phase.description}

**Required Deliverables for this Phase**:
"""

        for artifact in phase.required_artifacts:
            enhancement += f"- {artifact.path}: {artifact.description}\n"

        enhancement += """
**Success Criteria**:
"""
        for criteria in phase.success_criteria:
            enhancement += f"- {criteria}\n"

        # Add context from previous phases if available
        if phase.context_data.get("previous_phases"):
            enhancement += """
**Context from Previous Phases**:
"""
            for prev_phase_id, prev_data in phase.context_data[
                "previous_phases"
            ].items():
                enhancement += f"\n**{prev_data['name']}**:\n"
                for artifact_name, content in prev_data.get("artifacts", {}).items():
                    if len(content) < 1000:
                        enhancement += f"- {artifact_name}:\n```\n{content}\n```\n"
                    else:
                        enhancement += f"- {artifact_name}: [Content available but too large to include]\n"

        enhancement += """
**CRITICAL REQUIREMENTS**:
- You MUST create and save all required deliverables to the specified paths
- Use the write_file tool to save your deliverables to the project directory
- Ensure all deliverables meet the success criteria listed above
- Build upon the context from previous phases when available

"""

        return f"{enhancement}\n{base_prompt}"

    def save_workflow_state(self) -> bool:
        """Save current workflow state to project directory"""
        if not self.current_pattern:
            return False

        state_file = self.project_path / "workflow_state.json"

        state_data = {
            "pattern_name": self.current_pattern.name,
            "pattern_version": self.current_pattern.version,
            "phases": {},
            "execution_log": self.phase_execution_log,
            "last_updated": datetime.now().isoformat(),
        }

        # Serialize phase data
        for phase_id, phase in self.current_pattern.phases.items():
            state_data["phases"][phase_id] = {
                "status": phase.status.value,
                "start_time": phase.start_time.isoformat()
                if phase.start_time
                else None,
                "completion_time": phase.completion_time.isoformat()
                if phase.completion_time
                else None,
            }

        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
            logger.info(f"Workflow state saved to: {state_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    def load_workflow_state(self) -> bool:
        """Load workflow state from project directory"""
        state_file = self.project_path / "workflow_state.json"

        if not state_file.exists():
            return False

        try:
            with open(state_file, encoding="utf-8") as f:
                state_data = json.load(f)

            # Load the pattern
            pattern = self.load_workflow_pattern(state_data["pattern_name"])
            if not pattern:
                logger.error(f"Could not load pattern: {state_data['pattern_name']}")
                return False

            self.current_pattern = pattern
            self.phase_execution_log = state_data.get("execution_log", [])

            # Restore phase states
            for phase_id, phase_state in state_data.get("phases", {}).items():
                if phase_id in self.current_pattern.phases:
                    phase = self.current_pattern.phases[phase_id]
                    phase.status = PhaseStatus(phase_state["status"])
                    if phase_state["start_time"]:
                        phase.start_time = datetime.fromisoformat(
                            phase_state["start_time"]
                        )
                    if phase_state["completion_time"]:
                        phase.completion_time = datetime.fromisoformat(
                            phase_state["completion_time"]
                        )

            logger.info(f"Workflow state loaded from: {state_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return False
