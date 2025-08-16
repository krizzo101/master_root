import pytest
from asea_factory.agents.requirements import RequirementsAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_requirements_agent_autonomous(config):
    agent = RequirementsAgent(config)
    requirements_input = {
        "functional": ["User can register", "User can login"],
        "non_functional": ["System responds in <2s"],
        "constraints": ["No PII stored"],
        "user_stories": ["As a user, I want to register so I can use the app."],
        "acceptance_criteria": ["Registration is successful with valid data."],
    }
    spec = agent.run(requirements_input=requirements_input)
    assert spec is not None
    assert len(spec.requirements) == 4
    assert spec.user_stories == ["As a user, I want to register so I can use the app."]
    assert spec.acceptance_criteria == ["Registration is successful with valid data."]
