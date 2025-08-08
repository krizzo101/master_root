"""Round-robin coordinator for opsvi-pipeline."""
from typing import Awaitable, Callable, Any, List
import itertools

class RoundRobinCoordinator:
    def __init__(self, workers: List[Callable[[Any], Awaitable[Any]]]) -> None:
        self._cycle = itertools.cycle(workers)

    async def dispatch(self, item: Any) -> Any:
        worker = next(self._cycle)
        return await worker(item)
