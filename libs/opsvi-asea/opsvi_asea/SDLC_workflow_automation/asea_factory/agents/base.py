# Base class for all agents in the SDLC Automation Factory
from typing import Any, Dict


class AgentBase:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, *args, **kwargs):
        raise NotImplementedError("Each agent must implement the run() method.")
