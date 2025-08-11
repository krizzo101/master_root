import pytest
from asea_factory.agents.architecture import ArchitectureAgent
from asea_factory.config.config_loader import ConfigLoader


@pytest.fixture
def config():
    return ConfigLoader(".env", "config.yml")


def test_architecture_agent(config):
    agent = ArchitectureAgent(config)
    requirements_ids = ["req-1", "req-2"]
    research_ids = ["res-1"]
    arch = agent.run(requirements_ids, research_ids)
    assert arch is not None
    assert hasattr(arch, "architecture")
    assert hasattr(arch, "traceability")
