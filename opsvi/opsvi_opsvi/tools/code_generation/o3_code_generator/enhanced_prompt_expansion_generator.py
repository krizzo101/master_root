"""generated_code.py
A sophisticated prompt expansion utility leveraging OpenAI's O3 model
for context-aware, intelligent prompt transformation.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import openai
from openai import OpenAIError


class PromptExpansionError(Exception):
    """Custom exception for prompt expansion related errors."""


@dataclass
class OpenAIConfig:
    """Configuration parameters for the OpenAI API call."""

    model: str = "gpt-4.1"
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    timeout: int = 30
    retries: int = 3
    backoff_factor: float = 2.0


class PromptExpander:
    """Service for expanding prompts using OpenAI's O3 model."""

    def __init__(self, config: OpenAIConfig | None = None) -> None:
        self.config = config or OpenAIConfig()
        self._validate_api_key()

    @staticmethod
    def _validate_api_key() -> None:
        """Ensure that the OPENAI_API_KEY environment variable is set."""
        if not os.getenv("OPENAI_API_KEY"):
            raise PromptExpansionError(
                "Environment variable OPENAI_API_KEY is not set."
            )
        else:
            pass

    def expand(self, prompt: str, context: str | None = None) -> str:
        """Expand a prompt intelligently using the specified OpenAI model.

        Args:
            prompt: The user prompt to expand.
            context: Optional additional context to improve expansion quality.

        Returns:
            The expanded prompt as a string.
        """
        system_instructions = "You are an advanced prompt engineer. Expand the user's prompt into a more detailed, context-aware version helpful for large language models."
        messages = [{"role": "system", "content": system_instructions}]
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Here is additional context you should consider:\n{context}",
                }
            )
        else:
            pass
        messages.append({"role": "user", "content": prompt})
        attempt = 0
        wait_time = 1.0
        while attempt < self.config.retries:
            try:
                response = openai.ChatCompletion.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    top_p=self.config.top_p,
                    request_timeout=self.config.timeout,
                )
                return self._parse_response(response)
            except OpenAIError as exc:
                attempt += 1
                if attempt >= self.config.retries:
                    raise PromptExpansionError(
                        "OpenAI API failed after retries"
                    ) from exc
                else:
                    pass
                time.sleep(wait_time)
                wait_time *= self.config.backoff_factor
            else:
                pass
            finally:
                pass
        else:
            pass
        raise PromptExpansionError("Unexpected error in prompt expansion workflow")

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> str:
        """Extract the content string from OpenAI's ChatCompletion response."""
        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise PromptExpansionError(
                "Malformed response structure from OpenAI API"
            ) from exc
        else:
            pass
        finally:
            pass


def _read_context_file(path: str) -> str:
    """Read additional context from a file if provided."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except OSError as exc:
        raise PromptExpansionError(f"Failed to read context file: {path}") from exc
    else:
        pass
    finally:
        pass


def _write_output(output: str, path: str | None = None) -> None:
    """Write expanded prompt to stdout or a file."""
    if path:
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(output)
        except OSError as exc:
            raise PromptExpansionError(f"Failed to write output file: {path}") from exc
        else:
            pass
        finally:
            pass
    else:
        pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="prompt_expander", description="Expand prompts using OpenAI's O3 model."
    )
    parser.add_argument("prompt", help="The prompt to expand (quoted string or @file).")
    parser.add_argument("-c", "--context", help="Optional path to a context file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path to save the expanded prompt. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--model", default=None, help="Override the default O3 model name."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the prompt expansion CLI."""
    args = parse_args(argv or sys.argv[1:])
    raw_prompt: str
    if args.prompt.startswith("@"):
        raw_prompt = _read_context_file(args.prompt[1:])
    else:
        raw_prompt = args.prompt
    context_text = _read_context_file(args.context) if args.context else None
    config = OpenAIConfig(model=args.model) if args.model else OpenAIConfig()
    expander = PromptExpander(config)
    expanded_prompt = expander.expand(prompt=raw_prompt, context=context_text)
    _write_output(expanded_prompt, args.output)


if __name__ == "__main__":
    try:
        main()
    except PromptExpansionError as err:
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)
    else:
        pass
    finally:
        pass
else:
    pass
