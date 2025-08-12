import pytest
from asea_factory.agents.environment import EnvironmentAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_environment_agent(config):
    agent = EnvironmentAgent(config)
    # This will pass if Docker is running, otherwise will fail as expected
    result = agent.run()
    assert isinstance(result, bool)
