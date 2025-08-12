import argparse
import json
import logging
import os
import sys

import openai


def setup_logging() -> None:
    """Set up the logging configuration for the script."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def expand_prompt(simple_prompt: str) -> str:
    """Expand a simple user prompt into a comprehensive, detailed prompt by calling the OpenAI API.

    This function uses the OpenAI API to intelligently expand a simple prompt into one that
    includes best practices, error handling, logging, comprehensive documentation, and adherence
    to PEP 8 standards.

    Args:
        simple_prompt (str): A simple user instruction or request.

    Returns:
        str: An expanded, detailed prompt suitable for generating high-quality production code.
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable not set."
            logging.error(error_msg)
            raise OSError(error_msg)
        else:
            pass
        openai.api_key = api_key
        model = os.getenv("O3_MODEL", "o3")
        system_message = "You are an expert AI that expands simple user prompts into detailed, comprehensive prompts designed for generating production-quality Python code. The expanded prompt must instruct the generation of code that follows best practices, includes thorough error handling, logging, detailed documentation and type hints, adheres to PEP 8 standards, and incorporates modular and reusable design."
        user_message = f"Expand the following prompt with all the necessary details for high-quality code generation:\n\n{simple_prompt}"
        logging.info("Calling OpenAI API for prompt expansion...")
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_completion_tokens=16000,
        )
        logging.info(f"Full response: {response}")
        logging.info(f"Response choices: {response.choices}")
        if response.choices:
            logging.info(f"First choice: {response.choices[0]}")
            logging.info(f"First choice message: {response.choices[0].message}")
        else:
            pass
        expanded = response.choices[0].message.content.strip()
        logging.info(
            f"Prompt has been expanded successfully using the OpenAI API. Length: {len(expanded)}"
        )
        logging.info(f"Expanded content: {expanded}")
        return expanded
    except Exception as oe:
        logging.error(f"OpenAI API error during prompt expansion: {oe}")
        raise
    except Exception as e:
        logging.error(f"An error occurred during prompt expansion: {e}")
        raise
    else:
        pass
    finally:
        pass


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the prompt expansion script.

    Returns:
        argparse.Namespace: Parsed command line arguments including the user prompt.
    """
    parser = argparse.ArgumentParser(
        description="Expand a simple user request or enhancement JSON into a comprehensive prompt for code generation."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--prompt",
        type=str,
        required=False,
        help="A simple user prompt that needs to be expanded.",
    )
    group.add_argument(
        "--json",
        type=str,
        required=False,
        help="Path to a JSON enhancement request file containing a 'prompt' field.",
    )
    return parser.parse_args()


def main() -> None:
    """The main function that runs the prompt expansion script."""
    setup_logging()
    args = parse_arguments()
    user_prompt: str | None = None
    if args.json:
        try:
            with open(args.json, encoding="utf-8") as f:
                data = json.load(f)
            user_prompt = data.get("prompt", None)
            if not user_prompt:
                logging.error(f"No 'prompt' field found in {args.json}.")
                sys.exit(1)
            else:
                pass
            logging.info(f"Loaded prompt from JSON file: {args.json}")
        except Exception as e:
            logging.error(f"Failed to load or parse JSON file {args.json}: {e}")
            sys.exit(1)
        else:
            pass
        finally:
            pass
    elif args.prompt:
        user_prompt = args.prompt
    else:
        try:
            user_prompt = input("Enter your simple prompt: ")
        except Exception as e:
            logging.error(f"Failed to read user input: {e}")
            sys.exit(1)
        else:
            pass
        finally:
            pass
    if not user_prompt or not user_prompt.strip():
        logging.error("Empty prompt received. Provide a valid prompt.")
        sys.exit(1)
    else:
        pass
    try:
        detailed_prompt = expand_prompt(user_prompt)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
