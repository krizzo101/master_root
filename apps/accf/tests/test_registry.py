import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)
from registry.registry import AgentRegistry


def test_registry_init():
    registry = AgentRegistry()
    assert isinstance(registry.agents, dict)


def test_registry_register_and_lookup():
    registry = AgentRegistry()
    registry.register("test_agent", ["test"], {"role": "tester"})
    agent = registry.lookup("test_agent")
    assert agent["capabilities"] == ["test"]
    assert agent["metadata"]["role"] == "tester"


def test_registry_list_agents():
    registry = AgentRegistry()
    registry.register("a1", ["c1"])
    registry.register("a2", ["c2"])
    agents = registry.list_agents()
    assert "a1" in agents and "a2" in agents
