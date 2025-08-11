import pytest
from asea_factory.agents.design_review import DesignReviewAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_design_review_agent(config):
    agent = DesignReviewAgent(config)
    architecture_id = "arch-1"
    review = agent.run(architecture_id)
    assert review is not None
    assert hasattr(review, "approval")
