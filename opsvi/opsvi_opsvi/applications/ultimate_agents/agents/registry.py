"""
Agent registry for discovery and dynamic instantiation of agent types.
"""


class AgentRegistry:
    """Placeholder for agent registry logic."""

    def __init__(self):
        self._agents = {}

    def register(self, name, agent_cls):
        self._agents[name] = agent_cls

    def get(self, name):
        return self._agents.get(name)
