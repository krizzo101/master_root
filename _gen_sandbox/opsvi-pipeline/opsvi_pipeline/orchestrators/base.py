"""Orchestrator base for opsvi-pipeline.

Provides a minimal DAG execution engine with async execution, simple recovery
support via checkpointing node completion, and typed APIs. Nodes are async
callables that accept a context dict and return a result. Edges are defined
by dependencies between node ids.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Set, Tuple

NodeFunc = Callable[[Dict[str, Any]], Awaitable[Any]]

__all__ = ["Orchestrator", "async_node", "NodeExecutionError"]


class NodeExecutionError(RuntimeError):
    """Raised when a node fails during execution."""

    def __init__(self, node_id: str, original: BaseException) -> None:
        self.node_id = node_id
        self.original = original
        super().__init__(f"Node '{node_id}' failed: {original!r}")


class Orchestrator:
    """Asynchronous DAG orchestrator with checkpointing.

    - Register nodes with add_node(node_id, func, deps)
    - Run with execute() which returns mapping of node_id -> result

    If a checkpoint dict is provided, completed node ids are read from it and
    skipped; new results are written back during execution.
    """

    def __init__(self, checkpoint: Optional[Dict[str, Any]] = None) -> None:
        # node_id -> (func, dependencies)
        self._nodes: Dict[str, Tuple[NodeFunc, List[str]]] = {}
        # results of nodes
        self._results: Dict[str, Any] = {}
        # checkpoint storage for completed node ids -> result
        self._checkpoint = checkpoint if checkpoint is not None else {}
        # lock for checkpoint updates
        self._lock = asyncio.Lock()

    def add_node(self, node_id: str, func: NodeFunc, deps: Optional[Iterable[str]] = None) -> None:
        """Register a node.

        node_id: unique identifier
        func: async callable accepting context dict
        deps: iterable of node_ids this node depends on
        """
        if node_id in self._nodes:
            raise ValueError(f"Node '{node_id}' already registered")
        deps_list = list(deps) if deps is not None else []
        if node_id in deps_list:
            raise ValueError(f"Node '{node_id}' cannot depend on itself")
        self._nodes[node_id] = (func, deps_list)

    async def _run_node(self, node_id: str) -> None:
        func, deps = self._nodes[node_id]
        # build context from dependency results
        context: Dict[str, Any] = {dep: self._results[dep] for dep in deps}
        result = await func(context)
        self._results[node_id] = result
        # checkpoint the result (store under node_id)
        async with self._lock:
            self._checkpoint[node_id] = result

    def _detect_cycle(self) -> None:
        # simple DFS cycle and validity detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {n: WHITE for n in self._nodes}

        def dfs(u: str) -> None:
            color[u] = GRAY
            for v in self._nodes[u][1]:
                if v not in self._nodes:
                    raise ValueError(f"Node '{u}' depends on unknown node '{v}'")
                if color[v] == GRAY:
                    raise ValueError(f"Cycle detected involving '{u}' and '{v}'")
                if color[v] == WHITE:
                    dfs(v)
            color[u] = BLACK

        for node in self._nodes:
            if color[node] == WHITE:
                dfs(node)

    async def execute(self, concurrency: int = 4) -> Dict[str, Any]:
        """Execute the DAG asynchronously.

        concurrency: max number of concurrently running tasks.
        Returns a dict mapping node_id to result (includes checkpointed results).
        """
        if concurrency < 1:
            raise ValueError("concurrency must be >= 1")
        if not self._nodes:
            return {}
        self._detect_cycle()

        # initialize results from checkpoint
        for nid, val in list(self._checkpoint.items()):
            if nid in self._nodes:
                self._results[nid] = val

        # compute reverse deps and unmet dependency counts
        dependents: Dict[str, List[str]] = {n: [] for n in self._nodes}
        unmet_count: Dict[str, int] = {}
        for n, (_, deps) in self._nodes.items():
            unmet = 0
            for d in deps:
                # _detect_cycle ensures d is a known node
                if d not in self._results:
                    unmet += 1
                dependents[d].append(n)
            unmet_count[n] = unmet

        # queue ready nodes
        ready: asyncio.Queue[str] = asyncio.Queue()
        for n, cnt in unmet_count.items():
            if cnt == 0 and n not in self._results:
                await ready.put(n)

        sem = asyncio.Semaphore(concurrency)
        running: Set[asyncio.Task[None]] = set()
        failed = asyncio.Event()
        first_exc: Optional[BaseException] = None

        async def worker(node_id: str) -> None:
            nonlocal first_exc
            try:
                async with sem:
                    await self._run_node(node_id)
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # capture any node failure
                if first_exc is None:
                    first_exc = NodeExecutionError(node_id, exc)
                failed.set()
                # re-raise to mark task failed
                raise
            # notify dependents only if succeeded
            for dep in dependents.get(node_id, []):
                unmet_count[dep] -= 1
                if unmet_count[dep] == 0 and dep not in self._results:
                    await ready.put(dep)

        # scheduler loop
        async def scheduler() -> None:
            nonlocal first_exc
            try:
                while True:
                    if failed.is_set() and not running:
                        break
                    if ready.empty() and not running:
                        break

                    try:
                        node_id = await asyncio.wait_for(ready.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        continue

                    if failed.is_set():
                        # stop scheduling new work
                        break

                    task = asyncio.create_task(worker(node_id))
                    running.add(task)

                    def _on_done(t: asyncio.Task[None]) -> None:
                        running.discard(t)

                    task.add_done_callback(_on_done)

                # cancel remaining tasks on failure
                if failed.is_set() and running:
                    for t in list(running):
                        t.cancel()
                if running:
                    await asyncio.gather(*running, return_exceptions=True)
            finally:
                # propagate first error if present
                if first_exc is not None:
                    raise first_exc

        await scheduler()
        return dict(self._results)

    def results(self) -> Dict[str, Any]:
        """Return a copy of the current results mapping."""
        return dict(self._results)


# Small convenience factory for synchronous functions
def async_node(fn: Callable[[Dict[str, Any]], Any]) -> NodeFunc:
    """Wrap a sync function into an async node function."""

    async def _wrapped(ctx: Dict[str, Any]) -> Any:
        return fn(ctx)

    return _wrapped
