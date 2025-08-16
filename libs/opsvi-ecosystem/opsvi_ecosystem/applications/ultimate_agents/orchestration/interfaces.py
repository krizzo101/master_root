"""
Protocols and interfaces for orchestration contracts.
"""

from typing import Protocol


class OrchestrationProtocol(Protocol):
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...
