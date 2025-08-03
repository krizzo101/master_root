import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)

from agent_base.agent_base import AgentBase


def test_agent_base_init():
    agent = AgentBase(name="test_agent")
    assert agent.name == "test_agent"
    assert isinstance(agent.config, dict)
    assert agent.state == {}
    assert agent.log == []


def test_agent_base_handle_message():
    agent = AgentBase(name="test_agent")
    response = agent.handle_message({"msg": "hello"})
    assert isinstance(response, dict)
    assert response["status"] == "not_implemented"


def test_agent_base_state():
    agent = AgentBase(name="test_agent")
    agent.update_state("foo", "bar")
    assert agent.get_state("foo") == "bar"


def test_agent_base_log_event():
    agent = AgentBase(name="test_agent")
    agent.log_event("event1")
    assert "event1" in agent.log
