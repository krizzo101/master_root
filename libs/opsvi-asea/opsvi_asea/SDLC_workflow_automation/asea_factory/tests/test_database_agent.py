import pytest
from asea_factory.agents.database import DatabaseAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_database_agent(config):
    agent = DatabaseAgent(config)
    requirements = ["req-1"]
    architecture_id = "arch-1"
    artifact = agent.run(requirements, architecture_id)
    assert artifact is not None
    assert hasattr(artifact, "code")
