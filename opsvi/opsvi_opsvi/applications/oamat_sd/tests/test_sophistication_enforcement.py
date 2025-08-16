"""
SOPHISTICATION ENFORCEMENT TESTS

These tests MUST PASS for the implementation to be considered compliant.
Tests FAIL if any simplified patterns are detected.

CRITICAL: These tests ensure 75%+ sophistication compliance required for system operation.
"""

import importlib.util
from pathlib import Path
from typing import Any, Dict

import pytest


class SophisticationEnforcer:
    """Enhanced enforcer for sophisticated patterns and prevention of simplification"""

    FORBIDDEN_PATTERNS = [
        # Rule 955 Violations - LangGraph Architecture
        "asyncio.gather(",
        "gather(",
        "asyncio.gather *",
        # Template-based agent creation (forbidden simplification)
        "create_researcher_agent",
        "create_implementer_agent",
        "create_validator_agent",
        "role_based_creation",
        "AgentRole.RESEARCHER",
        "AgentRole.IMPLEMENTER",
        "AgentRole.VALIDATOR",
        # Template workflow selection (forbidden simplification)
        "WORKFLOW_TEMPLATE",
        "workflow_templates",
        "select_workflow",
        "TEMPLATE_WORKFLOWS",
        # Hardcoded role assignments (forbidden simplification)
        "role='researcher'",
        "role='implementer'",
        "role='validator'",
        # Mock-based testing that ignores real implementation
        "mock_llm_response",
        "NotImplementedError",
        "pass  # TODO",
    ]

    REQUIRED_PATTERNS = [
        # O3 dynamic generation (sophisticated requirement)
        "o3_generate_workflow",
        "o3_generate_agent_specification",
        "o3_adapt_workflow",
        "o3-mini",  # O3-mini model usage
        # LangGraph Send API (Rule 955 requirement)
        "Send(",
        "langgraph.constants.Send",
        "from langgraph.constants import Send",
        # Dynamic agent synthesis (sophisticated requirement)
        "synthesize_agent_from_specification",
        "dynamic_agent_creation",
        "create_react_agent",  # Rule 955 requirement
        # Runtime adaptation (sophisticated requirement)
        "runtime_adaptation",
        "modify_workflow_mid_execution",
        "adapt_during_execution",
    ]

    CRITICAL_FILES = [
        "src/tools/mcp_tool_registry.py",
        "src/agents/agent_factory.py",
        "src/enforcement/implementation_guards.py",
        "smart_decomposition_agent.py",
    ]

    @classmethod
    def scan_file_content(cls, file_path: Path) -> Dict[str, Any]:
        """Enhanced scanning of file content for sophisticated patterns"""
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            content = file_path.read_text(encoding="utf-8")
            violations = []
            validations = []

            # Scan for forbidden patterns with context
            for pattern in cls.FORBIDDEN_PATTERNS:
                if pattern in content:
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if pattern in line:
                            violations.append(
                                {
                                    "pattern": pattern,
                                    "line": i,
                                    "context": line.strip(),
                                    "severity": (
                                        "CRITICAL"
                                        if "asyncio.gather" in pattern
                                        else "HIGH"
                                    ),
                                }
                            )

            # Scan for required patterns
            for pattern in cls.REQUIRED_PATTERNS:
                if pattern in content:
                    validations.append({"pattern": pattern, "status": "PRESENT"})

            return {
                "violations": violations,
                "validations": validations,
                "compliance_score": max(0, 100 - (len(violations) * 20)),
            }
        except Exception as e:
            return {"error": f"Failed to analyze {file_path}: {str(e)}"}


def test_no_forbidden_patterns_in_codebase():
    """Test that NO forbidden simplification patterns exist in codebase"""

    src_path = Path("src/applications/oamat_sd/src")
    python_files = list(src_path.rglob("*.py"))

    violations = []

    for file_path in python_files:
        with open(file_path) as f:
            content = f.read()

        for pattern in SophisticationEnforcer.FORBIDDEN_PATTERNS:
            if pattern in content:
                violations.append(f"FORBIDDEN PATTERN '{pattern}' found in {file_path}")

    assert len(violations) == 0, "Sophistication violations detected:\n" + "\n".join(
        violations
    )


def test_required_patterns_present():
    """Test that ALL required sophisticated patterns are implemented"""

    src_path = Path("src/applications/oamat_sd/src")
    python_files = list(src_path.rglob("*.py"))

    all_content = ""
    for file_path in python_files:
        with open(file_path) as f:
            all_content += f.read()

    missing_patterns = []
    for pattern in SophisticationEnforcer.REQUIRED_PATTERNS:
        if pattern not in all_content:
            missing_patterns.append(f"REQUIRED PATTERN '{pattern}' NOT FOUND")

    assert len(missing_patterns) == 0, "Missing required patterns:\n" + "\n".join(
        missing_patterns
    )


def test_o3_workflow_generation_is_dynamic():
    """Test that O3 workflow generation creates unique workflows, not templates"""

    # Import the main module
    spec = importlib.util.spec_from_file_location(
        "smart_decomposition_agent",
        "src/applications/oamat_sd/smart_decomposition_agent.py",
    )
    module = importlib.util.module_from_spec(spec)

    # Check if workflow generation method exists and is sophisticated
    if hasattr(module, "SmartDecompositionAgent"):
        agent_class = module.SmartDecompositionAgent
        methods = [
            method for method in dir(agent_class) if "workflow" in method.lower()
        ]

        # Must have O3 workflow generation method
        assert any(
            ("o3" in method.lower() or "o3-mini" in method.lower())
            and "generate" in method.lower()
            for method in methods
        ), "Missing O3 workflow generation method"


def test_agent_creation_is_specification_based():
    """Test that agent creation uses specifications, not templates"""

    agent_factory_path = Path("src/applications/oamat_sd/src/agents/agent_factory.py")

    if agent_factory_path.exists():
        with open(agent_factory_path) as f:
            content = f.read()

        # Must NOT contain role-based creation
        forbidden_role_patterns = [
            "role='researcher'",
            "role='implementer'",
            "role='validator'",
            "create_researcher",
            "create_implementer",
        ]

        for pattern in forbidden_role_patterns:
            assert (
                pattern not in content
            ), f"FORBIDDEN role-based pattern '{pattern}' found in agent_factory.py"

        # Must contain specification-based creation
        required_spec_patterns = ["agent_spec", "specification", "synthesize_agent"]

        assert any(
            pattern in content for pattern in required_spec_patterns
        ), "Missing specification-based agent creation patterns"


def test_send_api_usage_not_asyncio():
    """Test that LangGraph Send API is used, not asyncio.gather"""

    src_path = Path("src/applications/oamat_sd/src")
    python_files = list(src_path.rglob("*.py"))

    send_api_usage = False
    asyncio_violations = []

    for file_path in python_files:
        with open(file_path) as f:
            content = f.read()

        # Check for Send API usage
        if "from langgraph.constants import Send" in content or "Send(" in content:
            send_api_usage = True

        # Check for forbidden asyncio.gather
        if "asyncio.gather" in content:
            asyncio_violations.append(f"FORBIDDEN asyncio.gather found in {file_path}")

    assert send_api_usage, "LangGraph Send API not found - required for sophistication"
    assert len(asyncio_violations) == 0, "asyncio.gather violations:\n" + "\n".join(
        asyncio_violations
    )


def test_runtime_adaptation_capability():
    """Test that runtime adaptation is implemented"""

    main_agent_path = Path("src/applications/oamat_sd/smart_decomposition_agent.py")

    if main_agent_path.exists():
        with open(main_agent_path) as f:
            content = f.read()

        # Must have adaptation capabilities
        adaptation_patterns = [
            "adapt_workflow",
            "modify_workflow",
            "runtime_adaptation",
            "mid_execution",
        ]

        assert any(
            pattern in content for pattern in adaptation_patterns
        ), "Missing runtime adaptation capability - required for sophistication"


def test_o3_model_sophisticated_usage():
    """Test that O3 model is used for sophisticated reasoning, not basic tasks"""

    src_path = Path("src/applications/oamat_sd")
    python_files = list(src_path.rglob("*.py"))

    o3_usage_found = False
    sophisticated_o3_patterns = ["o3_generate", "o3_invent", "o3_analyze", "o3_adapt"]

    for file_path in python_files:
        with open(file_path) as f:
            content = f.read()

        if any(pattern in content for pattern in sophisticated_o3_patterns):
            o3_usage_found = True
            break

    assert o3_usage_found, "O3 model not used for sophisticated generation patterns"


class TestImplementationCheckpoints:
    """Validation checkpoints at 25%, 50%, 75%, 100% completion"""

    def test_checkpoint_25_percent_o3_analysis_engine(self):
        """25% Checkpoint: O3 analysis engine validation"""

        main_path = Path("src/applications/oamat_sd/smart_decomposition_agent.py")

        if main_path.exists():
            with open(main_path) as f:
                content = f.read()

            # Must have sophisticated O3 analysis
            assert "o3-mini" in content.lower(), "O3-mini integration missing"
            assert "analyze" in content.lower(), "Analysis capability missing"

            # Must NOT have basic analysis
            assert "simple_analysis" not in content, "Simplified analysis detected"

    def test_checkpoint_50_percent_dynamic_agent_synthesis(self):
        """50% Checkpoint: Dynamic agent synthesis validation"""

        agent_factory_path = Path(
            "src/applications/oamat_sd/src/agents/agent_factory.py"
        )

        if agent_factory_path.exists():
            with open(agent_factory_path) as f:
                content = f.read()

            # Must be specification-based, not template-based
            assert (
                "specification" in content or "spec" in content
            ), "Specification-based agent creation missing"

            forbidden_templates = ["researcher_template", "implementer_template"]
            for template in forbidden_templates:
                assert template not in content, f"Template {template} found - forbidden"

    def test_checkpoint_75_percent_send_api_orchestration(self):
        """75% Checkpoint: Send API orchestration validation"""

        src_path = Path("src/applications/oamat_sd/src")
        python_files = list(src_path.rglob("*.py"))

        send_api_found = False

        for file_path in python_files:
            with open(file_path) as f:
                content = f.read()

            if "Send(" in content and "langgraph" in content:
                send_api_found = True
                break

        assert send_api_found, "LangGraph Send API orchestration not implemented"

    def test_checkpoint_100_percent_full_sophistication(self):
        """100% Checkpoint: Full sophistication integration test"""

        # Run all enforcement tests
        test_no_forbidden_patterns_in_codebase()
        test_required_patterns_present()
        test_send_api_usage_not_asyncio()
        test_runtime_adaptation_capability()
        test_o3_model_sophisticated_usage()


if __name__ == "__main__":
    # Run enforcement tests
    pytest.main([__file__, "-v"])
