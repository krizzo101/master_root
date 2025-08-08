"""Simple workflow for opsvi-agents (linear steps)."""
from typing import Awaitable, Callable, Any, List

class SimpleWorkflow:
    def __init__(self, steps: List[Callable[[], Awaitable[Any]]]) -> None:
        self.steps = steps

    async def run(self) -> None:
        for step in self.steps:
            await step()
