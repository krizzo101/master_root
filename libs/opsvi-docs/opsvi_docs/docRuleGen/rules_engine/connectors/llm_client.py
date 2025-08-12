# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"LLM Client Module","description":"This module provides a unified interface for interacting with various Large Language Model providers including OpenAI and Anthropic.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Documentation for the LLM Client Module.","line_start":2,"line_end":6},{"name":"Imports","description":"Import statements for required libraries and modules.","line_start":8,"line_end":12},{"name":"Global Variables","description":"Definition of global variables used in the module.","line_start":14,"line_end":14},{"name":"Function: is_provider_available","description":"Checks if a specified LLM provider is available.","line_start":16,"line_end":66},{"name":"Function: get_completion","description":"Retrieves a completion from the specified LLM provider.","line_start":68,"line_end":116},{"name":"Function: _get_openai_completion","description":"Handles the API call to OpenAI to get a completion.","line_start":118,"line_end":175},{"name":"Function: _get_anthropic_completion","description":"Handles the API call to Anthropic to get a completion.","line_start":177,"line_end":235}],"key_elements":[{"name":"is_provider_available","description":"Function to check if an LLM provider is available.","line":19},{"name":"get_completion","description":"Function to get a completion from an LLM provider.","line":69},{"name":"_get_openai_completion","description":"Function to get a completion from OpenAI.","line":118},{"name":"_get_anthropic_completion","description":"Function to get a completion from Anthropic.","line":176},{"name":"_available_providers","description":"Global variable to track available LLM providers.","line":14},{"name":"logger","description":"Logger instance for logging information and warnings.","line":13}]}
"""
# FILE_MAP_END

"""
LLM Client Module.

This module provides a unified interface for interacting with various
Large Language Model providers including OpenAI and Anthropic.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Track available LLM providers
_available_providers = {}


def is_provider_available(provider_name: str) -> bool:
    """
    Check if an LLM provider is available.

    Args:
        provider_name: Name of the provider (openai, anthropic)

    Returns:
        True if available, False otherwise
    """
    global _available_providers

    if provider_name in _available_providers:
        return _available_providers[provider_name]

    available = False

    # Check for OpenAI
    if provider_name.lower() == "openai":
        try:
            import openai

            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                available = True
                logger.info("OpenAI provider is available")
            else:
                logger.warning("OpenAI API key not found in environment variables")
        except ImportError:
            logger.warning("OpenAI package not installed. Run: pip install openai")

    # Check for Anthropic
    elif provider_name.lower() == "anthropic":
        try:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                available = True
                logger.info("Anthropic provider is available")
            else:
                logger.warning("Anthropic API key not found in environment variables")
        except ImportError:
            logger.warning(
                "Anthropic package not installed. Run: pip install anthropic"
            )

    else:
        logger.warning(f"Unknown provider: {provider_name}")

    # Cache result
    _available_providers[provider_name] = available
    return available


def get_completion(
    messages: List[Dict[str, str]],
    provider: str = "openai",
    model: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    retries: int = 3,
    retry_delay: int = 5,
    json_response: bool = False,
) -> str:
    """
    Get a completion from an LLM provider.

    Args:
        messages: List of message dictionaries with role and content
        provider: Provider name (openai, anthropic)
        model: Model name (if None, uses provider default)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        retries: Number of retries on failure
        retry_delay: Delay between retries in seconds
        json_response: Whether to request a JSON response

    Returns:
        Text completion from the model

    Raises:
        ValueError: If provider is invalid or unavailable
        Exception: If LLM API call fails after retries
    """
    if not is_provider_available(provider):
        raise ValueError(f"Provider '{provider}' is not available")

    for attempt in range(retries):
        try:
            if provider.lower() == "openai":
                return _get_openai_completion(
                    messages, model, max_tokens, temperature, json_response
                )
            elif provider.lower() == "anthropic":
                return _get_anthropic_completion(
                    messages, model, max_tokens, temperature, json_response
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(
                    f"LLM API call failed (attempt {attempt+1}/{retries}): {str(e)}"
                )
                time.sleep(retry_delay)
            else:
                logger.error(f"LLM API call failed after {retries} attempts: {str(e)}")
                raise


def _get_openai_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    json_response: bool = False,
) -> str:
    """
    Get a completion from OpenAI.

    Args:
        messages: List of message dictionaries
        model: Model name (defaults to gpt-4o-mini)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        json_response: Whether to request a JSON response

    Returns:
        Text completion
    """
    import openai

    # Set up client
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Use default model if not specified
    model = model or "gpt-4o-mini"

    # Prepare response format
    response_format = {"type": "json_object"} if json_response else None

    # Call API
    start_time = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
    )
    elapsed_time = time.time() - start_time

    # Log response details
    logger.info(f"OpenAI API call completed in {elapsed_time:.2f}s using model {model}")

    # Extract and return content
    if response.choices and len(response.choices) > 0:
        content = response.choices[0].message.content
        # Ensure the content is always a string, even for JSON responses
        if content is not None:
            if isinstance(content, (dict, list)):
                # Convert non-string content to JSON string
                logger.debug("Converting non-string content to JSON string")
                return json.dumps(content)
            return content
        return ""
    return ""


def _get_anthropic_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    json_response: bool = False,
) -> str:
    """
    Get a completion from Anthropic.

    Args:
        messages: List of message dictionaries
        model: Model name (defaults to claude-3-haiku)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        json_response: Whether to request a JSON response

    Returns:
        Text completion
    """
    import anthropic

    # Set up client
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Use default model if not specified
    model = model or "claude-3-haiku-20240307"

    # Convert OpenAI-style messages to Anthropic format
    anthropic_messages = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            # System message in Anthropic is set separately
            system_message = content
        elif role == "user":
            anthropic_messages.append({"role": "user", "content": content})
        elif role == "assistant":
            anthropic_messages.append({"role": "assistant", "content": content})

    # Prepare response format
    response_format = "json" if json_response else None

    # Call API
    start_time = time.time()
    response = client.messages.create(
        model=model,
        messages=anthropic_messages,
        system=system_message if "system_message" in locals() else None,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
    )
    elapsed_time = time.time() - start_time

    # Log response details
    logger.info(
        f"Anthropic API call completed in {elapsed_time:.2f}s using model {model}"
    )

    # Return content
    return response.content[0].text if response.content else ""
