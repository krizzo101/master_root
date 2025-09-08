"""
Working Quality Gates System
Integrates with current GenericOrchestrator to provide real validation
Built on proven working orchestrator foundation
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .generic_orchestrator import AgentTask
except ImportError:
    from generic_orchestrator import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of quality gate validation"""

    passed: bool
    issues: List[str]
    warnings: List[str] = None
    gate_name: str = ""
    validation_time: float = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class QualityGate(ABC):
    """Abstract quality gate for task validation"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def validate_pre_execution(self, task: AgentTask) -> ValidationResult:
        """Validate task before execution"""
        pass

    @abstractmethod
    async def validate_post_execution(self, task: AgentTask) -> ValidationResult:
        """Validate task after execution"""
        pass


class TaskStructureGate(QualityGate):
    """Validates basic task structure and requirements"""

    def __init__(self):
        super().__init__("task_structure")

    async def validate_pre_execution(self, task: AgentTask) -> ValidationResult:
        """Validate task has required structure before execution"""
        issues = []
        warnings = []

        # Required fields
        if not task.task_id or task.task_id.strip() == "":
            issues.append("Missing or empty task_id")
        if not task.task_type or task.task_type.strip() == "":
            issues.append("Missing or empty task_type")
        if not task.prompt or task.prompt.strip() == "":
            issues.append("Missing or empty prompt")

        # Task type validation
        valid_types = {
            # Architecture & Design
            "security-architect",
            "solution-architect",
            "requirements-analyst",
            # Development & Testing
            "development-specialist",
            "qa-testing-guru",
            "performance-optimizer",
            # Integration & Data
            "api-integration-specialist",
            "database-specialist",
            # Analysis & Documentation
            "business-analyst",
            "technical-writer",
            "research-genius",
            "code-analyzer",
            # Legacy types (for backward compatibility)
            "general-purpose",
            "web-scraper",
            "data-processor",
            "file-processor",
            "api-caller",
            "validation",
            "monitoring",
            # Legacy simple types (for backward compatibility)
            "research",
            "design",
            "code",
            "test",
            "review",
            "documentation",
            "analysis",
            "optimization",
            "integration",
            "deployment",
        }
        if task.task_type not in valid_types:
            warnings.append(
                f"Unusual task_type '{task.task_type}', expected one of: {valid_types}"
            )

        # Prompt quality checks
        if len(task.prompt) < 10:
            warnings.append("Prompt is very short - may not provide sufficient context")
        if len(task.prompt) > 2000:
            warnings.append("Prompt is very long - may exceed model limits")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name=self.name,
        )

    async def validate_post_execution(self, task: AgentTask) -> ValidationResult:
        """Validate task execution results"""
        issues = []
        warnings = []

        if task.status == "completed":
            if not task.result:
                issues.append("Task marked completed but has no result")
            elif not isinstance(task.result, dict):
                warnings.append("Task result is not a dictionary format")
        elif task.status == "failed":
            if not task.error:
                warnings.append("Task marked failed but has no error message")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name=self.name,
        )


class DependencyGate(QualityGate):
    """Validates task dependencies are properly structured"""

    def __init__(self):
        super().__init__("dependencies")

    async def validate_pre_execution(self, task: AgentTask) -> ValidationResult:
        """Validate dependencies before execution"""
        issues = []
        warnings = []

        # Check for self-dependency
        if task.task_id in task.dependencies:
            issues.append(f"Task {task.task_id} depends on itself")

        # Check for duplicate dependencies
        if len(task.dependencies) != len(set(task.dependencies)):
            duplicates = [
                dep
                for dep in set(task.dependencies)
                if task.dependencies.count(dep) > 1
            ]
            warnings.append(f"Duplicate dependencies found: {duplicates}")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name=self.name,
        )

    async def validate_post_execution(self, task: AgentTask) -> ValidationResult:
        """No post-execution validation needed for dependencies"""
        return ValidationResult(passed=True, issues=[], gate_name=self.name)


class PromptQualityGate(QualityGate):
    """Validates prompt quality and completeness"""

    def __init__(self):
        super().__init__("prompt_quality")

    async def validate_pre_execution(self, task: AgentTask) -> ValidationResult:
        """Validate prompt quality"""
        issues = []
        warnings = []

        prompt = task.prompt.lower()

        # Check for vague prompts
        vague_indicators = ["please", "can you", "help me", "just", "simple", "basic"]
        vague_count = sum(1 for indicator in vague_indicators if indicator in prompt)
        if vague_count >= 3:
            warnings.append("Prompt appears vague - may not produce specific results")

        # Check for actionable content
        action_words = [
            "implement",
            "create",
            "build",
            "design",
            "analyze",
            "research",
            "test",
            "validate",
            "optimize",
            "refactor",
            "document",
        ]
        has_action = any(action in prompt for action in action_words)
        if not has_action:
            warnings.append("Prompt lacks clear action words - may be unclear to agent")

        # Check for context
        context_indicators = ["based on", "using", "following", "according to", "with"]
        has_context = any(indicator in prompt for indicator in context_indicators)
        if not has_context and len(task.context) == 0:
            warnings.append("Prompt lacks context - agent may need more information")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name=self.name,
        )

    async def validate_post_execution(self, task: AgentTask) -> ValidationResult:
        """Validate prompt effectiveness based on results"""
        issues = []
        warnings = []

        if task.status == "completed" and task.result:
            # Check if result seems to match the task type
            result_str = str(task.result).lower()

            if task.task_type == "code" and "code" not in result_str:
                warnings.append(
                    "Code task completed but result doesn't appear to contain code"
                )
            elif task.task_type == "research" and len(result_str) < 100:
                warnings.append("Research task result is very short")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name=self.name,
        )


class QualityGateManager:
    """Manages quality gates integration with GenericOrchestrator"""

    def __init__(self, enabled_gates: List[str] = None):
        self.gates = {
            "structure": TaskStructureGate(),
            "dependencies": DependencyGate(),
            "prompt": PromptQualityGate(),
        }

        # Enable specific gates or all by default
        if enabled_gates:
            self.active_gates = {
                name: gate for name, gate in self.gates.items() if name in enabled_gates
            }
        else:
            self.active_gates = self.gates

        logger.info(f"Quality gates initialized: {list(self.active_gates.keys())}")

    async def validate_pre_execution(
        self, task: AgentTask
    ) -> Dict[str, ValidationResult]:
        """Run all pre-execution validations"""
        results = {}

        for name, gate in self.active_gates.items():
            try:
                result = await gate.validate_pre_execution(task)
                results[name] = result

                if not result.passed:
                    logger.warning(
                        f"Quality gate '{name}' failed for task {task.task_id}: {result.issues}"
                    )
                elif result.warnings:
                    logger.info(
                        f"Quality gate '{name}' warnings for task {task.task_id}: {result.warnings}"
                    )

            except Exception as e:
                logger.error(
                    f"Quality gate '{name}' error for task {task.task_id}: {e}"
                )
                results[name] = ValidationResult(
                    passed=False,
                    issues=[f"Gate execution error: {str(e)}"],
                    gate_name=name,
                )

        return results

    async def validate_post_execution(
        self, task: AgentTask
    ) -> Dict[str, ValidationResult]:
        """Run all post-execution validations"""
        results = {}

        for name, gate in self.active_gates.items():
            try:
                result = await gate.validate_post_execution(task)
                results[name] = result

                if not result.passed:
                    logger.warning(
                        f"Post-execution gate '{name}' failed for task {task.task_id}: {result.issues}"
                    )
                elif result.warnings:
                    logger.info(
                        f"Post-execution gate '{name}' warnings for task {task.task_id}: {result.warnings}"
                    )

            except Exception as e:
                logger.error(
                    f"Post-execution gate '{name}' error for task {task.task_id}: {e}"
                )
                results[name] = ValidationResult(
                    passed=False,
                    issues=[f"Gate execution error: {str(e)}"],
                    gate_name=name,
                )

        return results

    def should_block_execution(
        self, validation_results: Dict[str, ValidationResult]
    ) -> bool:
        """Determine if task execution should be blocked based on validation results"""
        for result in validation_results.values():
            if not result.passed:
                return True
        return False

    async def generate_validation_report(
        self,
        task: AgentTask,
        pre_results: Dict[str, ValidationResult],
        post_results: Dict[str, ValidationResult] = None,
    ) -> str:
        """Generate human-readable validation report"""
        report = [f"Quality Gate Report for Task: {task.task_id}"]
        report.append("=" * 50)

        # Pre-execution results
        report.append("\nPre-execution Validation:")
        for name, result in pre_results.items():
            status = "✓ PASS" if result.passed else "✗ FAIL"
            report.append(f"  {name}: {status}")

            if result.issues:
                for issue in result.issues:
                    report.append(f"    - Issue: {issue}")

            if result.warnings:
                for warning in result.warnings:
                    report.append(f"    - Warning: {warning}")

        # Post-execution results if available
        if post_results:
            report.append("\nPost-execution Validation:")
            for name, result in post_results.items():
                status = "✓ PASS" if result.passed else "✗ FAIL"
                report.append(f"  {name}: {status}")

                if result.issues:
                    for issue in result.issues:
                        report.append(f"    - Issue: {issue}")

                if result.warnings:
                    for warning in result.warnings:
                        report.append(f"    - Warning: {warning}")

        return "\n".join(report)


# Integration hooks for GenericOrchestrator
def create_quality_gate_hooks(quality_manager: QualityGateManager):
    """Create hooks for integrating quality gates with GenericOrchestrator"""

    async def pre_execute_hook(task: AgentTask):
        """Pre-execution hook for quality gates"""
        validation_results = await quality_manager.validate_pre_execution(task)

        # Store validation results in task context for later reference
        task.context["quality_gate_pre_results"] = {
            name: {
                "passed": result.passed,
                "issues": result.issues,
                "warnings": result.warnings,
            }
            for name, result in validation_results.items()
        }

        # Block execution if critical issues found
        if quality_manager.should_block_execution(validation_results):
            report = await quality_manager.generate_validation_report(
                task, validation_results
            )
            logger.error(f"Quality gates blocked task {task.task_id}:\n{report}")
            task.status = "failed"
            task.error = "Failed quality gate validation"

    async def post_execute_hook(task: AgentTask):
        """Post-execution hook for quality gates"""
        validation_results = await quality_manager.validate_post_execution(task)

        # Store post-execution results
        task.context["quality_gate_post_results"] = {
            name: {
                "passed": result.passed,
                "issues": result.issues,
                "warnings": result.warnings,
            }
            for name, result in validation_results.items()
        }

        # Generate full report
        pre_results = {}
        if "quality_gate_pre_results" in task.context:
            pre_results = {
                name: ValidationResult(
                    passed=data["passed"],
                    issues=data["issues"],
                    warnings=data["warnings"],
                    gate_name=name,
                )
                for name, data in task.context["quality_gate_pre_results"].items()
            }

        report = await quality_manager.generate_validation_report(
            task, pre_results, validation_results
        )

        logger.info(f"Quality gate report for {task.task_id}:\n{report}")

    return pre_execute_hook, post_execute_hook


# Testing function
async def test_quality_gates():
    """Test quality gates with sample tasks"""
    logger.info("Testing quality gates system...")

    # Create quality gate manager
    manager = QualityGateManager()

    # Test tasks
    good_task = AgentTask(
        task_id="good_task",
        task_type="code",
        prompt="Implement a function to calculate factorial using recursion with proper error handling",
        dependencies=[],
    )

    bad_task = AgentTask(
        task_id="",  # Missing task_id
        task_type="",  # Missing task_type
        prompt="do something",  # Vague prompt
        dependencies=["bad_task"],  # Self dependency
    )

    # Test good task
    print("\n=== Testing Good Task ===")
    pre_results = await manager.validate_pre_execution(good_task)
    report = await manager.generate_validation_report(good_task, pre_results)
    print(report)

    # Test bad task
    print("\n=== Testing Bad Task ===")
    pre_results = await manager.validate_pre_execution(bad_task)
    report = await manager.generate_validation_report(bad_task, pre_results)
    print(report)

    print(f"\nShould block bad task: {manager.should_block_execution(pre_results)}")


if __name__ == "__main__":
    asyncio.run(test_quality_gates())
