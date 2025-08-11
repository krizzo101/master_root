"""
Protocols and interfaces for agent contracts.
"""

from typing import Any, Protocol


class AgentProtocol(Protocol):
    def act(self, *args, **kwargs) -> Any:
        ...

    def observe(self, *args, **kwargs) -> None:
        ...
