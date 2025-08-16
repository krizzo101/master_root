import pytest
from asea_factory.agents.backend import BackendAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_backend_agent(config):
    agent = BackendAgent(config)
    requirements = ["req-1"]
    architecture_id = "arch-1"
    artifact = agent.run(requirements, architecture_id)
    assert artifact is not None
    assert hasattr(artifact, "code")
