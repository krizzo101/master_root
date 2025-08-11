import pytest
from asea_factory.agents.research import ResearchAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_research_agent(config):
    agent = ResearchAgent(config)
    queries = ["Best practices for user authentication"]
    findings = agent.run(queries)
    assert findings is not None
    assert isinstance(findings, list)
    assert len(findings) > 0
    assert hasattr(findings[0], "summary")
