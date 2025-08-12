import pytest
from asea_factory.agents.testing import TestingAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_testing_agent(config):
    agent = TestingAgent(config)
    artifact_id = "a1"
    requirements = ["req-1"]
    suite = agent.run(artifact_id, requirements)
    assert suite is not None
    assert hasattr(suite, "results")
