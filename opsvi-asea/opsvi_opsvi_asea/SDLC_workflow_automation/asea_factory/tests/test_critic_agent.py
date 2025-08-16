import pytest
from asea_factory.agents.critic import CriticAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_critic_agent(config):
    agent = CriticAgent(config)
    artifact_id = "a1"
    code = "def foo():\n    return 42"
    review = agent.run(artifact_id, code)
    assert review is not None
    assert hasattr(review, "review")
