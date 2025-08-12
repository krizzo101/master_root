import pytest
from asea_factory.agents.management import ManagementAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_management_agent(config):
    agent = ManagementAgent(config)

    # Simulate a simple task orchestration
    class DummyAgent:
        def run(self, **kwargs):
            return "ok"

    tasks = [{"agent": DummyAgent(), "args": {}}]
    result = agent.run(tasks)
    assert result["results"][0] == "ok"
