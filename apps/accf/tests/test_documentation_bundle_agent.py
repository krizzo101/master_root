import asyncio
import logging
import os
import sys

import yaml

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)
from capabilities.documentation_bundle_agent import (
    DocumentationBundleAgent,
)
from schemas import (
    DocsBundle,
)


def test_docs_bundle_parallel():
    agent = DocumentationBundleAgent()
    prompt = "Generate docs for a todo app."
    bundle = asyncio.run(agent.generate_docs_bundle(prompt, mode="parallel"))
    assert isinstance(bundle, DocsBundle)
    assert bundle.requirements.title == "Requirements Document"
    assert bundle.design.title == "Design Document"
    assert bundle.specs.title == "Specs Document"
    assert bundle.test_plan.title == "Test Plan Document"


def test_docs_bundle_sequential():
    agent = DocumentationBundleAgent()
    prompt = "Generate docs for a todo app."
    bundle = asyncio.run(agent.generate_docs_bundle(prompt, mode="sequential"))
    assert isinstance(bundle, DocsBundle)
    assert bundle.requirements.title == "Requirements Document"
    assert bundle.design.title == "Design Document"
    assert bundle.specs.title == "Specs Document"
    assert bundle.test_plan.title == "Test Plan Document"


def test_logging_and_config(monkeypatch, tmp_path):
    # Patch config path
    config_path = tmp_path / "documentation_bundle_config.yaml"
    config = {
        "agent_types": ["requirements", "design", "specs", "test_plan", "user_guide"],
        "max_parallel_tasks": 2,
    }
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    monkeypatch.setenv("DOC_BUNDLE_CONFIG", str(config_path))
    agent = DocumentationBundleAgent()
    assert agent.max_parallel_tasks == 2
    assert "user_guide" in agent.agent_types
    # Patch logger to capture logs
    logs = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            logs.append(self.format(record))

    handler = ListHandler()
    agent.logger.addHandler(handler)
    prompt = "Test logging and config."
    try:
        asyncio.run(agent.generate_docs_bundle(prompt, mode="parallel"))
    except Exception:
        pass  # user_guide is a stub, may fail schema
    assert any("Loaded agent_types" in log for log in logs)
    assert any("Starting docs bundle generation" in log for log in logs)


def test_resource_management(monkeypatch):
    # Set max_parallel_tasks to 1 to force sequential execution
    monkeypatch.setenv("DOC_BUNDLE_MAX_PARALLEL", "1")
    agent = DocumentationBundleAgent()
    assert agent.max_parallel_tasks == 1
    prompt = "Test resource management."
    bundle = asyncio.run(agent.generate_docs_bundle(prompt, mode="parallel"))
    assert isinstance(bundle, DocsBundle)
    # Reset env
    monkeypatch.delenv("DOC_BUNDLE_MAX_PARALLEL", raising=False)
