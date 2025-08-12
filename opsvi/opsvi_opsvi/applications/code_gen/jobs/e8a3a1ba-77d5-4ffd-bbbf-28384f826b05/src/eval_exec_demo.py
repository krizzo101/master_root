"""
Script Demonstrating eval() and exec() Usage

This script shows safe and basic examples of using eval() and exec() in Python.
Both are powerful functions, but must be used with great care and never on untrusted input.
Refer to the in-code comments for explanations.
"""

import logging
import sys
from typing import Any


def demonstrate_eval() -> Any:
    """
    Demonstrates use of eval() to evaluate a simple, static Python expression.
    No user input is involved to ensure safety.
    Returns the result of evaluation.
    """
    # Here we define a simple mathematical expression as a string.
    expression = "(2 + 3) * 4"
    logging.info("Evaluating expression using eval(): %s", expression)

    # Evaluate the expression safely (since it's hardcoded and not from user input).
    # eval() parses the expression and returns its result.
    result = eval(expression)
    return result


def demonstrate_exec() -> dict:
    """
    Demonstrates use of exec() to execute a block of Python code.
    The code block creates variables and does some computations.
    Returns a dictionary of the resulting local namespace for inspection.
    """
    # Define a multi-line code block as a string.
    code_block = (
        "x = 10\n"  # Define x
        "y = 20\n"  # Define y
        "z = x * y\n"  # Compute z as the product
        "print(f'Inside exec() block: x={x}, y={y}, z={z}')"
    )
    logging.info("Executing code block using exec():\n%s", code_block)

    # We'll use a dictionary to capture the local namespace after execution.
    local_namespace = {}

    # Exec executes the statements but does not return a value.
    # We supply a local namespace so we can inspect variables defined in the code block.
    exec(code_block, {}, local_namespace)
    return local_namespace


def main() -> None:
    """
    Main entry point. Demonstrates usage of eval() and exec(), prints outputs with explanations.
    """
    # Set up basic logging to standard output
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    print("=== Demonstration of eval() ===")
    try:
        eval_result = demonstrate_eval()
        print(f'Result of eval("(2 + 3) * 4"): {eval_result}')
        print("# eval() evaluated the mathematical expression and returned the result.")
    except Exception as e:
        logging.error("Error during eval demonstration: %s", e)
        sys.exit(1)

    print("\n=== Demonstration of exec() ===")
    try:
        local_ns = demonstrate_exec()
        # Show the variables defined by the exec() code block
        print(f"Variables after exec(): { {k: v for k, v in local_ns.items()} }")
        print(
            "# exec() executed the code block, defined variables x, y, z, and printed their values."
        )
    except Exception as e:
        logging.error("Error during exec demonstration: %s", e)
        sys.exit(1)

    print("\nScript execution complete.")


if __name__ == "__main__":
    main()
