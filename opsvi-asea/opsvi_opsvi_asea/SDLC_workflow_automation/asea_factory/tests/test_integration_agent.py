import pytest
from asea_factory.agents.integration import IntegrationAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_integration_agent(config):
    agent = IntegrationAgent(config)

    class DummyArtifact:
        id = "a1"

    artifacts = [DummyArtifact(), DummyArtifact(), DummyArtifact()]
    artifact = agent.run(artifacts)
    assert artifact is not None
    assert hasattr(artifact, "code")
