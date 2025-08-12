import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from generate_content import (
    CriticAgent,
    DesignAgent,
    PromptSynthesizer,
    RequirementsAgent,
    SpecAgent,
    SummarizerAgent,
    ValidatorAgent,
    load_agent_prompt_schema,
    remediate_context_summary,
    remediate_design,
    remediate_input_validation,
    remediate_planning,
    remediate_requirements,
    remediate_spec,
)


@pytest.fixture
def agent_prompt_file(tmp_path):
    prompt_path = tmp_path / "prompt.yaml"
    prompt_path.write_text(
        """
title: Test Task
description: Test description
objectives: [Test objective]
requirements: [Test requirement]
constraints: []
context_files: []
referenced_files: []
standards: []
onboarding: ''
artifact_types: [code, doc]
output_preferences: {format: markdown, language: python}
"""
    )
    return str(prompt_path)


def test_input_validation_and_remediation(agent_prompt_file):
    agent_prompt = load_agent_prompt_schema(agent_prompt_file)
    validator = ValidatorAgent()
    errors, warnings, context_blobs = validator.validate(
        agent_prompt.title, agent_prompt.context_files
    )
    validation_report = f"User prompt: {repr(agent_prompt.title)}\nContext files: {agent_prompt.context_files}\nErrors: {errors}\nWarnings: {warnings}"
    critic = CriticAgent()
    review, _ = critic.review(validation_report, "input validation report")
    remediated = remediate_input_validation(
        validation_report, ["Critical: Example issue"]
    )
    assert "AUTO-REMEDIATION" in remediated


def test_context_summarization_and_remediation():
    summarizer = SummarizerAgent()
    with patch.object(
        SummarizerAgent, "summarize", return_value=("Test summary", ["trace"])
    ):
        context_summary, _ = summarizer.summarize(["Test context"])
        critic = CriticAgent()
        review, _ = critic.review(context_summary, "context summary")
        remediated = remediate_context_summary(
            context_summary, ["Major: Example issue"]
        )
        assert "AUTO-REMEDIATION" in remediated


def test_requirements_extraction_and_remediation():
    requirements_agent = RequirementsAgent()
    req_doc, _ = requirements_agent.extract("Test prompt", "Test context summary")
    critic = CriticAgent()
    review, _ = critic.review(req_doc, "requirements document")
    remediated = remediate_requirements(req_doc, ["Minor: Example issue"])
    assert "AUTO-REMEDIATION" in remediated


def test_design_and_remediation():
    design_agent = DesignAgent()
    design_doc, _ = design_agent.design("Test requirements doc")
    critic = CriticAgent()
    review, _ = critic.review(design_doc, "design document")
    remediated = remediate_design(design_doc, ["Critical: Example issue"])
    assert "AUTO-REMEDIATION" in remediated


def test_spec_and_remediation():
    spec_agent = SpecAgent()
    spec_doc, _ = spec_agent.spec("Test requirements doc", "Test design doc")
    critic = CriticAgent()
    review, _ = critic.review(spec_doc, "spec document")
    remediated = remediate_spec(spec_doc, ["Major: Example issue"])
    assert "AUTO-REMEDIATION" in remediated


def test_planning_and_remediation():
    planning_agent = PromptSynthesizer()
    planning_doc, _ = planning_agent.synthesize(
        "Test requirements doc", "Test design doc", "Test spec doc"
    )
    critic = CriticAgent()
    review, _ = critic.review(planning_doc, "planning prompt")
    remediated = remediate_planning(planning_doc, ["Minor: Example issue"])
    assert "AUTO-REMEDIATION" in remediated


def test_checkpointing(tmp_path):
    # Input validation checkpoint
    from generate_content import (
        load_input_validation_checkpoint,
        save_input_validation_checkpoint,
    )

    save_input_validation_checkpoint("test input validation checkpoint")
    assert load_input_validation_checkpoint() == "test input validation checkpoint"
    # Context summary checkpoint
    from generate_content import (
        load_context_summary_checkpoint,
        save_context_summary_checkpoint,
    )

    save_context_summary_checkpoint("test context summary checkpoint")
    assert load_context_summary_checkpoint() == "test context summary checkpoint"
    # Design checkpoint
    from generate_content import load_design_checkpoint, save_design_checkpoint

    save_design_checkpoint("test design checkpoint")
    assert load_design_checkpoint() == "test design checkpoint"
    # Spec checkpoint
    from generate_content import load_spec_checkpoint, save_spec_checkpoint

    save_spec_checkpoint("test spec checkpoint")
    assert load_spec_checkpoint() == "test spec checkpoint"
    # Planning checkpoint
    from generate_content import load_planning_checkpoint, save_planning_checkpoint

    save_planning_checkpoint("test planning checkpoint")
    assert load_planning_checkpoint() == "test planning checkpoint"


def test_validator_agent_edge_cases():
    validator = ValidatorAgent()
    # Test with empty prompt
    errors, warnings, context_blobs = validator.validate("", [])
    assert errors
    # Test with invalid context file
    errors, warnings, context_blobs = validator.validate(
        "Test", ["nonexistent_file.md"]
    )
    assert warnings or errors


def test_remediation_edge_cases():
    # Test remediation with empty issues
    assert remediate_input_validation("report", []) == "report"
    assert remediate_context_summary("summary", []) == "summary"
    assert remediate_requirements("req", []) == "req"
    assert remediate_design("design", []) == "design"
    assert remediate_spec("spec", []) == "spec"
    assert remediate_planning("plan", []) == "plan"
    # Test remediation with multiple issues
    result = remediate_input_validation("report", ["Issue1", "Issue2"])
    assert result.count("AUTO-REMEDIATION") == 2


def test_checkpointing_edge_cases(tmp_path):
    # Remove checkpoint files if they exist
    for fname in [
        ".input_validation_checkpoint.pkl",
        ".context_summary_checkpoint.pkl",
        ".design_checkpoint.pkl",
        ".spec_checkpoint.pkl",
        ".planning_checkpoint.pkl",
    ]:
        try:
            os.remove(fname)
        except FileNotFoundError:
            pass
    from generate_content import (
        load_context_summary_checkpoint,
        load_design_checkpoint,
        load_input_validation_checkpoint,
        load_planning_checkpoint,
        load_spec_checkpoint,
    )

    assert load_input_validation_checkpoint() is None
    assert load_context_summary_checkpoint() is None
    assert load_design_checkpoint() is None
    assert load_spec_checkpoint() is None
    assert load_planning_checkpoint() is None


def test_critic_agent_review_edge_cases():
    critic = CriticAgent()
    # Test with empty doc
    review, trace = critic.review("", "requirements document")
    assert isinstance(review, str)
    # Test with non-string doc_type
    review, trace = critic.review("Some doc", 123)
    assert isinstance(review, str)


def test_agent_prompt_schema_validation():
    from prompt_schema import AgentPromptSchema

    # Missing required fields
    schema = AgentPromptSchema(title="", description="", objectives=[], requirements=[])
    errors = schema.validate()
    assert errors
    # Valid schema
    schema = AgentPromptSchema(
        title="T", description="D", objectives=["O"], requirements=["R"]
    )
    errors = schema.validate()
    assert not errors
