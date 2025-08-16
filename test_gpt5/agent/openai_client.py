import json
import os
from collections.abc import Callable, Iterable
from typing import Any, cast

from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class OpenAIClientError(Exception):
    pass


class OpenAIClient:
    """Light wrapper around OpenAI Responses API with tool orchestration.

    - Reads API key from env OPENAI_API_KEY (never logs it)
    - Supports previous_response_id to maintain reasoning context
    - Handles streaming events and routes function tool calls
    """

    def __init__(
        self,
        model: str = "gpt-5",
        reasoning_effort: str = "medium",
        verbosity: str = "low",
        parallel_tool_calls: bool = True,
        request_timeout: float = 120.0,
    ) -> None:
        if "OPENAI_API_KEY" not in os.environ:
            raise OpenAIClientError("OPENAI_API_KEY not set in environment")
        # Let the SDK read the API key from environment
        self.client = OpenAI()
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.parallel_tool_calls = parallel_tool_calls
        self.request_timeout = request_timeout

    @retry(  # type: ignore[misc]
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def create_response(
        self,
        input_items: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        previous_response_id: str | None = None,
        stream: bool = True,
    ) -> Iterable[Any]:
        """Create a response; returns an iterator of stream events when stream=True.

        input_items: Responses API input array (message/tool_result/etc.)
        tools: optional function tools
        previous_response_id: continue context from prior call
        """
        params: dict[str, Any] = {
            "model": self.model,
            "input": input_items,
            "stream": stream,
            "parallel_tool_calls": self.parallel_tool_calls,
            "verbosity": self.verbosity,
        }
        # only include when provided
        if tools:
            params["tools"] = tools
        if previous_response_id:
            params["previous_response_id"] = previous_response_id
        # reasoning effort (if supported by model)
        if self.reasoning_effort:
            params["reasoning_effort"] = self.reasoning_effort

        # NOTE: openai-python streams are sync iterables when stream=True
        # Some SDK versions may not support newer params (e.g., reasoning_effort, verbosity).
        # Retry without them when TypeError indicates unexpected kwargs.
        try:
            events = cast(Iterable[Any], self.client.responses.create(**params))
        except TypeError as e:
            msg = str(e)
            cleaned_params = dict(params)
            retried = False
            for k in ("reasoning_effort", "verbosity"):
                if k in cleaned_params and ("unexpected keyword" in msg or k in msg):
                    cleaned_params.pop(k, None)
                    retried = True
            if retried:
                events = cast(
                    Iterable[Any], self.client.responses.create(**cleaned_params)
                )
            else:
                raise
        if stream:
            return events  # iterator of events
        return [events]

    def tool_loop(
        self,
        initial_items: list[dict[str, Any]],
        tool_defs: list[dict[str, Any]],
        tool_router: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
        max_rounds: int = 8,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Run streaming loop, executing function tools and feeding outputs back.

        Returns (final_text, transcript_items)
        """
        items: list[dict[str, Any]] = list(initial_items)
        last_response_id: str | None = None
        final_text_parts: list[str] = []

        for _ in range(max_rounds):
            events = self.create_response(
                input_items=items if last_response_id is None else [items[-1]],
                tools=tool_defs,
                previous_response_id=last_response_id,
                stream=True,
            )

            pending_function_call: dict[str, Any] | None = None
            tool_call_done = False
            for event in events:
                etype = getattr(event, "type", None)
                if etype == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if isinstance(delta, str):
                        final_text_parts.append(delta)
                elif etype == "response.output_item.added":
                    item = getattr(event, "item", None)
                    if item and getattr(item, "type", None) == "function_call":
                        pending_function_call = {
                            "id": getattr(item, "id", None),
                            "name": getattr(item, "name", None),
                            "arguments": getattr(item, "arguments", ""),
                        }
                elif etype == "response.function_call_arguments.delta":
                    if pending_function_call is not None:
                        pending_function_call["arguments"] = pending_function_call.get(
                            "arguments", ""
                        ) + getattr(event, "delta", "")
                elif etype == "response.function_call_arguments.done":
                    tool_call_done = True
                elif etype == "response.completed":
                    # capture response id for continuity
                    response = getattr(event, "response", None)
                    if response is not None:
                        last_response_id = getattr(response, "id", last_response_id)
                # ignore other event types

            if pending_function_call and tool_call_done:
                # Execute tool
                name = pending_function_call.get("name")
                args_json = pending_function_call.get("arguments", "") or "{}"
                try:
                    parsed_args = json.loads(args_json)
                except Exception:
                    parsed_args = {}
                if name not in tool_router:
                    tool_output = {"error": f"Unknown tool: {name}"}
                else:
                    tool_output = tool_router[name](parsed_args)
                # Feed tool output back
                tool_result_item = {
                    "type": "function_call_output",
                    "call_id": pending_function_call.get("id"),
                    "output": json.dumps(tool_output),
                    "status": "completed",
                }
                items = [tool_result_item]
                # continue loop with previous_response_id
                continue

            # No more tools requested; finish
            break

        return ("".join(final_text_parts).strip(), items)
