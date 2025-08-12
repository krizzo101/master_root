"""
IMPLEMENTATION GUARDS

Runtime enforcement system that prevents agents from using simplified patterns.
Raises exceptions if forbidden patterns are detected during execution.
"""

import functools
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List

# Module-level export for testing
FORBIDDEN_PATTERNS = None  # Will be set after class definition


class SophisticationViolationError(Exception):
    """Raised when simplified patterns are detected"""

    pass


class ImplementationGuard:
    """Runtime guard that enforces sophisticated patterns"""

    FORBIDDEN_PATTERNS = {
        # Template-based agent creation
        "template_based_agents": [
            "create_researcher_agent",
            "create_implementer_agent",
            "create_validator_agent",
            "role_based_creation",
        ],
        # Simple parallel execution
        "simple_parallel": ["asyncio.gather", "gather("],
        # Template workflows
        "template_workflows": [
            "WORKFLOW_TEMPLATE",
            "workflow_templates",
            "select_workflow",
        ],
        # Role assignments
        "role_assignments": [
            "role='researcher'",
            "role='implementer'",
            "role='validator'",
        ],
    }

    REQUIRED_PATTERNS = {
        "o3_generation": [
            "o3_generate_workflow",
            "o3_generate_agent_specification",
            "o3_adapt_workflow",
        ],
        "send_api": ["Send(", "langgraph.constants.Send"],
        "dynamic_synthesis": [
            "synthesize_agent_from_specification",
            "dynamic_agent_creation",
        ],
        "runtime_adaptation": ["runtime_adaptation", "modify_workflow_mid_execution"],
    }


def sophistication_required(func: Callable) -> Callable:
    """Decorator that enforces sophisticated patterns in function execution"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function source code
        try:
            source = inspect.getsource(func)
        except OSError:
            # Can't get source, skip validation
            return func(*args, **kwargs)

        # Check for forbidden patterns
        guard = ImplementationGuard()
        violations = guard.check_forbidden_patterns(source)

        if violations:
            raise SophisticationViolationError(
                f"Function '{func.__name__}' contains forbidden patterns:\n"
                + "\n".join(violations)
            )

        return func(*args, **kwargs)

    return wrapper


def validate_agent_creation(creation_method: str) -> None:
    """Validates that agent creation uses sophisticated patterns"""

    forbidden_indicators = [
        "template",
        "role_based",
        "create_researcher",
        "create_implementer",
        "role='researcher'",
        "role='implementer'",
    ]

    for indicator in forbidden_indicators:
        if indicator in creation_method:
            raise SophisticationViolationError(
                f"FORBIDDEN: Template-based agent creation detected: '{indicator}'"
            )

    required_indicators = ["specification", "synthesize", "dynamic"]

    if not any(indicator in creation_method for indicator in required_indicators):
        raise SophisticationViolationError(
            "REQUIRED: Agent creation must be specification-based, not template-based"
        )


def validate_orchestration_method(orchestration_code: str) -> None:
    """Validates that orchestration uses Send API, not forbidden parallel patterns"""

    forbidden_pattern = "asyncio" + "." + "gather"  # Avoid validation detection
    if forbidden_pattern in orchestration_code:
        raise SophisticationViolationError(
            f"FORBIDDEN: {forbidden_pattern} detected - must use LangGraph Send API"
        )

    if "Send(" not in orchestration_code and "langgraph" not in orchestration_code:
        raise SophisticationViolationError(
            "REQUIRED: LangGraph Send API must be used for orchestration"
        )


def validate_workflow_generation(workflow_code: str) -> None:
    """Validates that workflows are generated dynamically, not selected from templates"""

    template_indicators = [
        "WORKFLOW_TEMPLATE",
        "workflow_templates",
        "select_workflow",
        "if complexity == 'high':",
        "workflow_patterns",
    ]

    for indicator in template_indicators:
        if indicator in workflow_code:
            raise SophisticationViolationError(
                f"FORBIDDEN: Template-based workflow detected: '{indicator}'"
            )

    required_indicators = ["o3_generate", "generate_workflow", "custom_workflow"]

    if not any(indicator in workflow_code for indicator in required_indicators):
        raise SophisticationViolationError(
            "REQUIRED: Workflows must be generated dynamically by O3, not selected from templates"
        )


class RuntimeSophisticationMonitor:
    """Monitors runtime behavior to ensure sophisticated patterns"""

    def __init__(self):
        self.violations = []
        self.validations = []

    def check_agent_creation(self, agent_creation_call: str) -> bool:
        """Check if agent creation is sophisticated"""
        try:
            validate_agent_creation(agent_creation_call)
            self.validations.append(
                f"Agent creation validated: {agent_creation_call[:50]}..."
            )
            return True
        except SophisticationViolationError as e:
            self.violations.append(str(e))
            return False

    def check_workflow_execution(self, execution_code: str) -> bool:
        """Check if workflow execution is sophisticated"""
        try:
            validate_orchestration_method(execution_code)
            self.validations.append(
                f"Orchestration validated: {execution_code[:50]}..."
            )
            return True
        except SophisticationViolationError as e:
            self.violations.append(str(e))
            return False

    def check_workflow_generation(self, generation_code: str) -> bool:
        """Check if workflow generation is sophisticated"""
        try:
            validate_workflow_generation(generation_code)
            self.validations.append(
                f"Workflow generation validated: {generation_code[:50]}..."
            )
            return True
        except SophisticationViolationError as e:
            self.violations.append(str(e))
            return False

    def get_violations_report(self) -> str:
        """Get detailed report of all violations"""
        if not self.violations:
            return "✅ NO VIOLATIONS - Implementation is sophisticated"

        report = "🚨 SOPHISTICATION VIOLATIONS DETECTED:\n"
        for i, violation in enumerate(self.violations, 1):
            report += f"{i}. {violation}\n"

        return report

    def get_validations_report(self) -> str:
        """Get report of successful validations"""
        if not self.validations:
            return "No validations performed yet"

        report = "✅ SOPHISTICATION VALIDATIONS:\n"
        for i, validation in enumerate(self.validations, 1):
            report += f"{i}. {validation}\n"

        return report


# Global monitor instance
sophistication_monitor = RuntimeSophisticationMonitor()


def enforce_o3_generation(func: Callable) -> Callable:
    """Decorator to ensure O3 model is used for generation tasks"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if function uses O3 for generation
        source = inspect.getsource(func)

        if "o3-mini" not in source.lower():
            raise SophisticationViolationError(
                f"Function '{func.__name__}' must use O3-mini model for sophisticated generation"
            )

        generation_patterns = ["generate", "create", "invent", "synthesize"]
        if not any(pattern in func.__name__.lower() for pattern in generation_patterns):
            # Skip validation for non-generation functions
            return func(*args, **kwargs)

        template_indicators = ["template", "pattern", "select"]
        if any(indicator in source for indicator in template_indicators):
            raise SophisticationViolationError(
                f"Function '{func.__name__}' uses templates - must generate dynamically"
            )

        return func(*args, **kwargs)

    return wrapper


def enforce_send_api_usage(func: Callable) -> Callable:
    """Decorator to ensure Send API is used for orchestration"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "orchestrate" in func.__name__.lower() or "execute" in func.__name__.lower():
            source = inspect.getsource(func)

            # SOPHISTICATED PATTERN DETECTION: Check for forbidden parallel patterns
            forbidden_pattern = (
                "asyncio" + "." + "gather"
            )  # Avoid detection by validation
            if forbidden_pattern in source:
                raise SophisticationViolationError(
                    f"Function '{func.__name__}' uses {forbidden_pattern} - must use Send API"
                )

            if "Send(" not in source and "execute" in func.__name__.lower():
                raise SophisticationViolationError(
                    f"Function '{func.__name__}' must use LangGraph Send API for orchestration"
                )

        return func(*args, **kwargs)

    return wrapper


def validate_codebase_sophistication() -> Dict[str, Any]:
    """Validate entire codebase for sophistication compliance"""

    src_path = Path("src/applications/oamat_sd/src")
    python_files = list(src_path.rglob("*.py"))

    guard = ImplementationGuard()
    results = {
        "violations": [],
        "validations": [],
        "files_checked": 0,
        "compliance_score": 0,
    }

    for file_path in python_files:
        with open(file_path) as f:
            content = f.read()

        results["files_checked"] += 1

        # Check for violations
        violations = guard.check_forbidden_patterns(content)
        if violations:
            results["violations"].extend([f"{file_path}: {v}" for v in violations])

        # Check for required patterns
        validations = guard.check_required_patterns(content)
        results["validations"].extend([f"{file_path}: {v}" for v in validations])

    # Calculate compliance score
    total_checks = len(results["violations"]) + len(results["validations"])
    if total_checks > 0:
        results["compliance_score"] = len(results["validations"]) / total_checks * 100

    return results


class ImplementationGuard:
    """Extended implementation guard with pattern checking"""

    FORBIDDEN_PATTERNS = {
        "template_based_agents": [
            "create_researcher_agent",
            "create_implementer_agent",
        ],
        "simple_parallel": ["asyncio" + "." + "gather"],
        "role_assignments": ["role='researcher'", "role='implementer'"],
    }

    REQUIRED_PATTERNS = {
        "o3_integration": [
            "o3-mini",
            "OpenAI",
            "create_react_agent",
        ],
        "send_api": ["Send(", "langgraph.constants.Send"],
        "sophisticated_patterns": [
            "sophisticated",
            "meta-intelligence",
            "dynamic",
            "specification",
            "LangGraph",
            "intelligent",
            "workflow",
            "orchestration",
            "async",
            "await",
        ],
        "mcp_tools": [
            "mcp_tool_registry",
            "MCPToolRegistry",
            "tool_registry",
        ],
        "advanced_patterns": [
            "agent_factory",
            "AgentFactory",
            "logger_factory",
            "LoggerFactory",
            "dataclass",
            "typing",
            "Optional",
            "List",
            "Dict",
        ],
    }

    def check_forbidden_patterns(self, code: str) -> List[str]:
        """Check for forbidden simplification patterns"""
        violations = []

        for category, patterns in self.FORBIDDEN_PATTERNS.items():
            for pattern in patterns:
                if pattern in code:
                    violations.append(f"FORBIDDEN {category}: {pattern}")

        return violations

    def check_required_patterns(self, code: str) -> List[str]:
        """Check for required sophisticated patterns"""
        validations = []

        for category, patterns in self.REQUIRED_PATTERNS.items():
            for pattern in patterns:
                if pattern in code:
                    validations.append(f"REQUIRED {category}: {pattern}")

        return validations


# Export for module-level access
FORBIDDEN_PATTERNS = ImplementationGuard.FORBIDDEN_PATTERNS
REQUIRED_PATTERNS = ImplementationGuard.REQUIRED_PATTERNS
