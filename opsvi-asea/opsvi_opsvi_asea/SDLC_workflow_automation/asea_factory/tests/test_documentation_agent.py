import pytest
from asea_factory.agents.documentation import DocumentationAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_documentation_agent(config):
    agent = DocumentationAgent(config)
    artifact_ids = ["a1", "a2"]
    requirements = ["req-1"]
    doc = agent.run(artifact_ids, requirements)
    assert doc is not None
    assert hasattr(doc, "documentation")
