import functools
import hashlib
import json
import os
import random
import threading
import time

import backoff
from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from .db_client import modify

# optional redis cache
try:
    import redis

    _redis_url = os.getenv("REDIS_URL")
    _redis = redis.from_url(_redis_url) if _redis_url else None
except ImportError:
    _redis = None


def _redis_get(key: str):
    if not _redis:
        return None
    val = _redis.get(key)
    return json.loads(val) if val else None


def _redis_set(key: str, value: dict, ttl: int = 86400):
    if _redis:
        _redis.set(key, json.dumps(value), ex=ttl)


client = OpenAI()

# simple token bucket per model
_rate_lock = threading.Lock()
_rate_state = {}


def _allow(model: str, tokens: int, limit_per_min: int = 90000):
    with _rate_lock:
        now = time.time()
        state = _rate_state.get(model, {"tokens": 0, "reset": now + 60})
        if now > state["reset"]:
            state = {"tokens": 0, "reset": now + 60}
        if state["tokens"] + tokens > limit_per_min:
            return False
        state["tokens"] += tokens
        _rate_state[model] = state
        return True


def _format_tools(tools_list):
    """Convert tools to the correct OpenAI API format"""
    if not tools_list:
        return None

    formatted_tools = []
    for tool in tools_list:
        if isinstance(tool, dict):
            if "name" in tool and "parameters" in tool:
                # This is a function definition, wrap it in tool format
                formatted_tools.append({"type": "function", "function": tool})
            elif "type" in tool and tool["type"] == "function":
                # Already in correct tool format
                formatted_tools.append(tool)
            else:
                # Assume it's a function definition
                formatted_tools.append({"type": "function", "function": tool})
        else:
            # Not a dict, might be a string or other format
            formatted_tools.append(tool)

    return formatted_tools


@backoff.on_exception(
    backoff.expo, (APITimeoutError, APIError, RateLimitError), max_tries=3
)
def call_openai(
    model: str,
    messages: list,
    tools: list = None,
    tool_choice: str = "auto",
    temperature: float = 0.7,
    max_tokens: int = 1500,
    **kwargs,
):
    """
    Modern OpenAI API call with proper tools format
    """

    # Estimate tokens for rate limiting
    estimated_tokens = sum(len(str(msg)) for msg in messages) // 4

    if not _allow(model, estimated_tokens):
        raise APIError("Rate limit exceeded")

    # Build request parameters
    request_params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs,
    }

    # Add tools if provided
    if tools:
        formatted_tools = _format_tools(tools)
        if formatted_tools:
            request_params["tools"] = formatted_tools
            request_params["tool_choice"] = tool_choice

    # Check cache first
    cache_key = None
    if temperature == 0:  # Only cache deterministic calls
        cache_key = hashlib.md5(
            json.dumps(request_params, sort_keys=True).encode()
        ).hexdigest()
        cached = _redis_get(cache_key)
        if cached:
            return cached

    try:
        response = client.chat.completions.create(**request_params)

        # Convert response to dict for consistency
        result = {
            "choices": [
                {
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                        "tool_calls": [],
                    },
                    "finish_reason": choice.finish_reason,
                }
                for choice in response.choices
            ],
            "usage": (
                {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None
            ),
        }

        # Handle tool calls in the response
        for i, choice in enumerate(response.choices):
            if choice.message.tool_calls:
                result["choices"][i]["message"]["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in choice.message.tool_calls
                ]

        # Cache the result
        if cache_key:
            _redis_set(cache_key, result)

        return result

    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise


# Legacy function for backward compatibility
def call_openai_with_functions(
    model: str, messages: list, functions: list = None, **kwargs
):
    """
    Backward compatibility wrapper - converts old functions format to new tools format
    """
    tools = None
    if functions:
        tools = [{"type": "function", "function": func} for func in functions]

    return call_openai(model=model, messages=messages, tools=tools, **kwargs)


@functools.lru_cache(maxsize=256)
def _cached_completion_hash(prompt_hash: str):
    return None  # placeholder for cached lookup


def _log_cost(resp, model, system, user, start_time):
    latency = time.time() - start_time
    try:
        prompt_hash = hashlib.sha256((system + user).encode()).hexdigest()
        modify(
            operation="insert",
            collection="metrics",
            document={
                "type": "prompt_analytics",
                "model": model,
                "prompt_hash": prompt_hash,
                "latency": latency,
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
    except Exception:
        pass

    # basic token logging
    if resp.usage:
        usage = resp.usage
        print(
            f"[OpenAI] prompt:{usage.prompt_tokens} | completion:{usage.completion_tokens}"
        )


@backoff.on_exception(
    backoff.expo, (APITimeoutError, APIError, RateLimitError), max_tries=3
)
def chat_structured(
    model: str, system: str, user: str, schema: dict = None, temperature: float = 0
):
    """
    Modern chat completion using Structured Outputs with response_format.
    This replaces the old function calling approach.
    """
    start = time.time()

    # Build messages
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    # Build request parameters
    request_params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    # Add structured output schema if provided
    if schema:
        # Convert function schema to response_format schema
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.get("name", "response"),
                "description": schema.get("description", "Structured response"),
                "schema": schema.get("parameters", schema),  # Handle both formats
                "strict": True,
            },
        }
        request_params["response_format"] = response_format

    # Estimate tokens for rate limiting
    total_tokens = len(system.split()) + len(user.split()) + 100
    if not _allow(model, total_tokens):
        time.sleep(random.uniform(1, 3))

    try:
        # Make the API call
        response = client.chat.completions.create(**request_params)

        # Calculate elapsed time
        elapsed = time.time() - start

        # Extract usage info
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        print(f"[OpenAI] prompt:{input_tokens} | completion:{output_tokens}")

        # Cache the response if Redis is available
        if _redis and elapsed > 2:  # Only cache slow responses
            cache_key = hashlib.md5(f"{model}:{system}:{user}".encode()).hexdigest()
            _redis_set(
                cache_key,
                {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "usage": usage.model_dump() if usage else None,
                },
            )

        message = response.choices[0].message

        # Handle refusals (safety-based rejections)
        if hasattr(message, "refusal") and message.refusal:
            return StructuredResponse(
                content=None,
                refusal=message.refusal,
                parsed=None,
                raw_response=response,
            )

        # Parse structured content if schema was provided
        parsed_content = None
        if schema and message.content:
            try:
                parsed_content = json.loads(message.content)
            except json.JSONDecodeError:
                # This shouldn't happen with structured outputs, but handle gracefully
                parsed_content = {
                    "error": "Failed to parse structured response",
                    "raw": message.content,
                }

        return StructuredResponse(
            content=message.content,
            refusal=None,
            parsed=parsed_content,
            raw_response=response,
        )

    except Exception as e:
        print(f"[OpenAI] Error: {e}")
        raise


class StructuredResponse:
    """Response wrapper for structured outputs"""

    def __init__(
        self,
        content: str = None,
        refusal: str = None,
        parsed: dict = None,
        raw_response=None,
    ):
        self.content = content
        self.refusal = refusal
        self.parsed = parsed
        self.raw_response = raw_response


# Backward compatibility function
def chat(model: str, system: str, user: str, tools=None, temperature: float = 0):
    """
    Backward compatibility wrapper - converts old tools format to new schema format
    """
    schema = None
    if tools and len(tools) > 0:
        # Convert first tool to schema format
        tool = tools[0]
        schema = {
            "name": tool.get("name", "response"),
            "description": tool.get("description", "Structured response"),
            "parameters": tool.get("parameters", {}),
        }

    return chat_structured(model, system, user, schema, temperature)


# Direct API call function for advanced usage
def call_openai(
    model: str, messages: list, response_format: dict = None, temperature: float = 0
):
    """Direct OpenAI API call with full control"""
    request_params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if response_format:
        request_params["response_format"] = response_format

    response = client.chat.completions.create(**request_params)
    return response.model_dump()
