"""
Protocols and interfaces for tooling contracts.
"""

from typing import Any, Protocol


class ToolingProtocol(Protocol):
    def execute(self, *args, **kwargs) -> Any:
        ...
