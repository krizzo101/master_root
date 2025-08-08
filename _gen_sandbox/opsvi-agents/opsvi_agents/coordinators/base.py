"""Coordinator base for opsvi-agents.

This module implements a lightweight, extendable Coordinator that drives
agent execution in an asynchronous fashion. It provides a sensible default
scheduling policy (round-robin) and simple contention resolution. The
implementation is conservative about what an "agent" looks like: an
agent can be an object exposing a coroutine method (run, execute, perform),
or a callable/coroutine itself. The Coordinator tries to discover how to
invoke each agent automatically.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import random
from typing import Any, Awaitable, Callable, Iterable, List, Optional

from opsvi_agents.core.base import OpsviAgentsManager

logger = logging.getLogger(__name__)

# Strategy type aliases
SchedulingStrategy = Callable[[List[Any], "Coordinator"], List[Any]]
ContentionStrategy = Callable[[List[Any], "Coordinator"], Awaitable[List[Any]] | List[Any]]


class Coordinator(OpsviAgentsManager):
    """Base coordinator that orchestrates agent execution.

    The Coordinator discovers agents from the manager, schedules them
    according to a simple policy, and runs them concurrently up to a
    configurable concurrency limit.

    Extend this class to provide custom scheduling or contention
    resolution strategies.
    """

    # Built-in strategies registry (can be extended at runtime)
    _scheduling_strategies: dict[str, SchedulingStrategy] = {}
    _contention_strategies: dict[str, ContentionStrategy] = {}

    def __init__(
        self,
        *,
        concurrency: int = 5,
        scheduling: str | SchedulingStrategy = "round_robin",
        contention: str | ContentionStrategy = "first",
    ) -> None:
        """Initialize coordinator.

        Args:
            concurrency: Maximum number of agents to run concurrently.
            scheduling: Scheduling strategy (name or callable).
            contention: Contention strategy (name or callable).
        """
        # Tolerant super init to accommodate varying base implementations.
        try:
            super().__init__()  # type: ignore[misc]
        except TypeError:
            super().__init__()  # type: ignore[misc]

        self.concurrency = max(1, int(concurrency))
        self.scheduling = scheduling
        self.contention = contention

        # Ensure defaults are present in registries
        self._ensure_default_strategies()

    # --- Public API ------------------------------------------------------------------------

    async def coordinate(self) -> None:
        """Run one coordination round across discovered agents.

        Discovers agents, resolves contention, schedules them, and invokes
        each agent concurrently (bounded by the configured concurrency).
        """
        agents = await self._discover_agents()
        if not agents:
            logger.debug("No agents discovered to coordinate.")
            return

        agents = await self._resolve_contention(agents)
        if not agents:
            logger.debug("No agents selected after contention resolution.")
            return

        agents = self._schedule(agents)

        sem = asyncio.Semaphore(self.concurrency)

        async def run_agent(agent: Any) -> None:
            async with sem:
                try:
                    await self._invoke_agent(agent)
                except Exception as exc:  # pragma: no cover
                    logger.exception("Agent %r failed during coordination: %s", agent, exc)

        tasks = [asyncio.create_task(run_agent(a)) for a in agents]
        if not tasks:
            return

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for t in tasks:
                if not t.done():
                    t.cancel()
            raise

    # --- Strategy registry management ------------------------------------------------------

    @classmethod
    def register_scheduling(cls, name: str, strategy: SchedulingStrategy) -> None:
        """Register a scheduling strategy by name."""
        cls._scheduling_strategies[name] = strategy

    @classmethod
    def register_contention(cls, name: str, strategy: ContentionStrategy) -> None:
        """Register a contention strategy by name."""
        cls._contention_strategies[name] = strategy

    @classmethod
    def _ensure_default_strategies(cls) -> None:
        if cls._scheduling_strategies:
            # assume defaults already loaded
            pass
        else:
            cls.register_scheduling("round_robin", _schedule_round_robin)
            cls.register_scheduling("fifo", _schedule_fifo)
            cls.register_scheduling("random", _schedule_random)
        if not cls._contention_strategies:
            cls.register_contention("first", _contention_first)
            cls.register_contention("all", _contention_all)
            cls.register_contention("first_ready", _contention_first_ready)
            cls.register_contention("unique", _contention_unique)

    # --- Helper discovery / invocation logic -----------------------------------------------

    async def _discover_agents(self) -> List[Any]:
        """Obtain agents from the manager via common conventions.

        Supports:
        - An attribute named 'agents' (iterable or awaitable of iterable)
        - A method 'get_agents' (sync or async) returning an iterable
        """
        # Prefer explicit attribute
        if hasattr(self, "agents"):
            agents_attr = getattr(self, "agents")
            if inspect.isawaitable(agents_attr):
                agents_iter = await agents_attr
                if isinstance(agents_iter, Iterable):
                    return list(agents_iter)
            if isinstance(agents_attr, Iterable):
                return list(agents_attr)

        # Next, prefer a get_agents method
        getter = getattr(self, "get_agents", None)
        if callable(getter):
            result = getter()
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, Iterable):
                return list(result)

        return []

    def _schedule(self, agents: List[Any]) -> List[Any]:
        """Return agents in scheduled order using the configured strategy."""
        if not agents:
            return []
        strategy = self.scheduling
        if callable(strategy):
            try:
                return list(strategy(list(agents), self))
            except Exception:  # pragma: no cover
                logger.exception("Custom scheduling strategy failed; falling back to FIFO.")
                return list(agents)
        # name-based lookup
        func = self._scheduling_strategies.get(str(strategy))
        if func is None:
            logger.debug("Unknown scheduling '%s'; using FIFO.", strategy)
            return list(agents)
        return func(list(agents), self)

    async def _resolve_contention(self, agents: List[Any]) -> List[Any]:
        """Apply the configured contention strategy to select agents."""
        if not agents:
            return []
        strategy = self.contention
        if callable(strategy):
            try:
                maybe = strategy(list(agents), self)
                return await maybe if inspect.isawaitable(maybe) else list(maybe)
            except Exception:  # pragma: no cover
                logger.exception("Custom contention strategy failed; allowing all agents.")
                return list(agents)
        func = self._contention_strategies.get(str(strategy))
        if func is None:
            logger.debug("Unknown contention '%s'; allowing all agents.", strategy)
            return list(agents)
        result = func(list(agents), self)
        return await result if inspect.isawaitable(result) else list(result)

    async def _invoke_agent(self, agent: Any) -> None:
        """Attempt to invoke the agent entry-point.

        Supported forms (in order):
        - Awaitable object (await directly)
        - Method on agent: run/execute/perform (await if awaitable)
        - Callable agent (await if returns awaitable)
        """
        if inspect.isawaitable(agent):
            await agent
            return

        for name in ("run", "execute", "perform"):
            meth = getattr(agent, name, None)
            if callable(meth):
                result = meth()
                if inspect.isawaitable(result):
                    await result
                return

        if callable(agent):
            result = agent()
            if inspect.isawaitable(result):
                await result
            return

        logger.debug("Agent %r is not callable/awaitable; skipping.", agent)

    # --- Utility ---------------------------------------------------------------------------

    async def _is_ready(self, agent: Any) -> bool:
        """Best-effort readiness probe via an optional ready() method/property."""
        ready = getattr(agent, "ready", None)
        if ready is None:
            return True
        try:
            val = ready() if callable(ready) else ready
            return bool(await val) if inspect.isawaitable(val) else bool(val)
        except Exception:  # pragma: no cover
            logger.debug("Agent %r readiness check failed; assuming not ready.", agent)
            return False


# --- Built-in strategies -------------------------------------------------------------------

def _schedule_round_robin(agents: List[Any], coord: Coordinator) -> List[Any]:
    try:
        idx = int(getattr(coord, "_last_index", 0))
    except Exception:
        idx = 0
    n = len(agents)
    ordered = agents[idx % n :] + agents[: idx % n]
    try:
        setattr(coord, "_last_index", (idx + 1) % n)
    except Exception:
        pass
    return ordered


def _schedule_fifo(agents: List[Any], coord: Coordinator) -> List[Any]:
    return list(agents)


def _schedule_random(agents: List[Any], coord: Coordinator) -> List[Any]:
    shuffled = list(agents)
    random.shuffle(shuffled)
    return shuffled


def _contention_first(agents: List[Any], coord: Coordinator) -> List[Any]:
    return [agents[0]] if agents else []


def _contention_all(agents: List[Any], coord: Coordinator) -> List[Any]:
    return list(agents)


async def _contention_first_ready(agents: List[Any], coord: Coordinator) -> List[Any]:
    for a in agents:
        if await coord._is_ready(a):
            return [a]
    return []


def _agent_key(agent: Any) -> Any:
    # Prefer explicit identifiers when present
    for attr in ("id", "name", "uid", "key"):
        if hasattr(agent, attr):
            try:
                return getattr(agent, attr)
            except Exception:
                continue
    return id(agent)


def _contention_unique(agents: List[Any], coord: Coordinator) -> List[Any]:
    seen: set[Any] = set()
    unique: List[Any] = []
    for a in agents:
        k = _agent_key(a)
        if k in seen:
            continue
        seen.add(k)
        unique.append(a)
    return unique
