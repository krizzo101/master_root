"""prompt_expansion_script.py

A utility script for expanding user prompts via the OpenAI API using the
current SDK interface (client.responses.create). This script initializes
the O3Logger, parses command-line arguments, calls the OpenAI API to
expand prompts, and writes or logs the output.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Final

from openai import OpenAI, OpenAIError

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

setup_logger(LogConfig())
__all__: list[str] = ["expand_prompt", "save_to_file", "parse_arguments", "main"]
DEFAULT_MODEL: Final[str] = os.getenv("OPENAI_MODEL", "gpt-4.1")
DEFAULT_SYSTEM_MESSAGE: Final[
    str
] = "You are a helpful assistant. Expand the user's prompt into a more detailed, context-rich version while preserving the original intent."
client: Final[OpenAI] = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def expand_prompt(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_message: str = DEFAULT_SYSTEM_MESSAGE,
    temperature: float = 0.7,
    max_tokens: int = 16000,
) -> str:
    """Expand a user prompt using the OpenAI API.

    Args:
        prompt: The raw user prompt to expand.
        model: The model name to use for completion.
        system_message: System instructions for the model.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.

    Returns:
        The expanded prompt as returned by the model.

    Raises:
        RuntimeError: If the OpenAI API call fails.
    """
    logger = get_logger()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.responses.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except OpenAIError as err:
        logger.log_error(f"OpenAI API request failed: {err}")
        raise RuntimeError(f"OpenAI API request failed: {err}") from err
    else:
        pass
    finally:
        pass
    return response.choices[0].message.content.strip()


def save_to_file(content: str, file_path: str | Path) -> None:
    """Save text content to a file.

    Args:
        content: Text to write.
        file_path: Destination path.

    Raises:
        RuntimeError: If writing to the file fails.
    """
    logger = get_logger()
    path = Path(file_path)
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as err:
        logger.log_error(f"Failed to write output to {path}: {err}")
        raise RuntimeError(f"Failed to write output to {path}: {err}") from err
    else:
        pass
    finally:
        pass


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of arguments (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Expand prompts via the OpenAI API using the new SDK format.\nIf no prompt is supplied as an argument, the script reads from stdin."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to expand")
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        help="Optional file path to write the expanded prompt",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=16000,
        help="Maximum tokens in response (default: 16000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the prompt expansion script."""
    logger = get_logger()
    try:
        args = parse_arguments(argv)
        if args.prompt is not None:
            prompt_text = args.prompt
        else:
            prompt_text = sys.stdin.read()
        if not prompt_text.strip():
            logger.log_error(
                "No prompt supplied. Provide a prompt or pipe text via stdin."
            )
            sys.exit(1)
        else:
            pass
        expanded = expand_prompt(
            prompt=prompt_text,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        if args.output_file:
            save_to_file(expanded, args.output_file)
        else:
            logger.log_info(expanded)
    except Exception as err:
        logger.log_error(f"An unexpected error occurred: {err}")
        raise
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
