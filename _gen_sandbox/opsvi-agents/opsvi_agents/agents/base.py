"""Agent base for opsvi-agents.

Provides a lightweight async-capable Agent base class with simple planning,
memory, and tool-use interfaces. Subclasses can override plan/act/recall
for custom behavior.
"""
from __future__ import annotations

import asyncio
import datetime
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from opsvi_agents.core.base import OpsviAgentsManager

# A tool can be a sync function returning str or an async function returning str
ToolCallable = Callable[..., Union[str, Awaitable[str]]]


class Agent(OpsviAgentsManager):
    """Base agent with minimal planning, memory, and tool-use support.

    The class provides simple in-memory memory storage, a very small planner
    that turns input text into plan-steps, and a tool registry that can run
    sync or async callables.

    Args:
        name: Optional human-readable agent name.
        initial_memory: Optional list of memory strings to seed the memory store.
        tools: Optional mapping of tool name to callable.
        *args, **kwargs: forwarded to parent class constructor.
    """

    def __init__(
        self,
        name: str = "agent",
        initial_memory: Optional[List[str]] = None,
        tools: Optional[Dict[str, ToolCallable]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Forward arguments to parent in case it requires initialization
        super().__init__(*args, **kwargs)
        self.name = name
        self._memory: List[Dict[str, Any]] = []
        if initial_memory:
            ts = datetime.datetime.utcnow()
            for text in initial_memory:
                self._memory.append({"text": text, "meta": {}, "ts": ts})
        self._tools: Dict[str, ToolCallable] = dict(tools or {})

    # ----- Memory API -----
    async def add_memory(self, text: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Store a text item in the agent's short-term memory.

        This is intentionally simple — just appends a timestamped entry.
        """
        entry = {"text": text, "meta": meta or {}, "ts": datetime.datetime.utcnow()}
        # keep append synchronous but expose async API for consistency
        self._memory.append(entry)

    async def recall(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top_k memory entries most relevant to the query.

        Uses a simple bag-of-words overlap scoring. Returns entries with
        keys 'text', 'meta', 'ts' ordered by decreasing relevance.
        """
        if not query or not self._memory:
            return []

        q_tokens = set(re.findall(r"\w+", query.lower()))
        scores: List[tuple[int, int]] = []  # (score, index)

        for i, entry in enumerate(self._memory):
            tokens = set(re.findall(r"\w+", entry["text"].lower()))
            # simple intersection size as score
            score = len(q_tokens & tokens)
            # bias more recent memories slightly
            age_seconds = (datetime.datetime.utcnow() - entry["ts"]).total_seconds()
            recency_bonus = 1 if age_seconds < 3600 else 0
            scores.append((score + recency_bonus, i))

        # sort by score desc then by index
        scores.sort(key=lambda x: (x[0], -x[1]), reverse=True)
        results: List[Dict[str, Any]] = []
        for score, idx in scores[:top_k]:
            if score <= 0:
                continue
            results.append(self._memory[idx])
        return results

    # ----- Tool registry API -----
    def register_tool(self, name: str, func: ToolCallable) -> None:
        """Register a tool function that can be invoked by the agent.

        Tool functions may be synchronous (return str) or async (return awaitable str).
        """
        if not callable(func):
            raise TypeError("tool must be callable")
        self._tools[name] = func

    def unregister_tool(self, name: str) -> None:
        """Remove a registered tool by name."""
        self._tools.pop(name, None)

    async def use_tool(self, name: str, *args: Any, **kwargs: Any) -> str:
        """Invoke a registered tool by name and return its result as a string.

        Raises KeyError if the tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"tool '{name}' not found")
        func = self._tools[name]
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)  # type: ignore[arg-type]
        else:
            # run sync functions in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(func, *args, **kwargs)
        if not isinstance(result, str):
            # Coerce to string for a consistent interface
            result = str(result)
        return result

    # ----- Planning API -----
    async def plan(self, input_data: str) -> List[str]:
        """Create a simple plan (list of steps) for the given input.

        Default planner: if a registered tool name appears in the input, create
        a tool-invocation step. Otherwise split input into sentence-like steps.
        Subclasses can override to provide smarter planning.
        """
        text = (input_data or "").strip()
        if not text:
            return []

        # if tools referenced explicitly as "<toolname>(...)", or simple word match
        for tool_name in self._tools.keys():
            # match whole word
            if re.search(rf"\b{re.escape(tool_name)}\b", text, re.IGNORECASE):
                # pass the whole text as argument to the tool as a convenience
                return [f"tool:{tool_name} {text}"]

        # fallback: split on punctuation into steps
        parts = [p.strip() for p in re.split(r"[\.\n;!?]+", text) if p.strip()]
        if not parts:
            return [text]
        return parts

    async def run_plan(self, plan_steps: List[str]) -> List[str]:
        """Execute plan steps sequentially and return a list of outputs.

        A plan step starting with "tool:<name>" will invoke the named tool with
        whitespace-split arguments. Other steps are treated as no-op reflections
        and returned as-is.
        """
        outputs: List[str] = []
        for step in plan_steps:
            step = step.strip()
            if step.lower().startswith("tool:"):
                _, rest = step.split(":", 1)
                tokens = rest.strip().split()
                if not tokens:
                    outputs.append("")
                    continue
                tool_name, *tool_args = tokens
                try:
                    res = await self.use_tool(tool_name, *tool_args)
                except Exception as exc:  # keep errors local to the step
                    res = f"<tool-error {tool_name}: {exc}>")
                outputs.append(res)
            else:
                # plain step; echo back
                outputs.append(step)
        return outputs

    # ----- Act API -----
    async def act(self, input_data: str) -> str:
        """Primary agent entrypoint.

        Default implementation: plan from input, store the plan in memory, and
        return the original input unchanged. Subclasses should override to
        implement real agent behavior (e.g., executing the plan and composing
        a response from outputs).
        """
        plan = await self.plan(input_data)
        if plan:
            # store a short representation of the plan
            await self.add_memory("last_plan: " + " | ".join(plan))
        return input_data


# End of file
