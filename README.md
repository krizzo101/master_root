Python Calculator (CLI)

Overview

- A small, safe, and modular command-line calculator written in Python.
- Supports standard arithmetic (+, -, *, /, //, %, **), parentheses, unary +/-, and a few functions (sqrt, abs, round).
- Safe parsing via Python's AST (no eval).
- REPL mode with history and an "ans" variable that remembers the last result.

Quick start

1) Install (editable install):

   pip install -e .

2) One-off calculation:

   pycalc "2 + 2 * (10 - 3)"

3) REPL mode:

   pycalc -i

   Commands inside REPL:
   - history: show previous expressions and results
   - quit or exit: leave the REPL

Options

- --precision N  Format output to N decimal places (default: 10)
- -i, --interactive  Start in interactive mode (REPL)

Examples

- pycalc "sqrt(9) + 4"
- pycalc "2 ** 10"
- pycalc --precision 4 "10 / 3"

Design

- calcapp/operations.py: Primitive numeric operations.
- calcapp/parser.py: Safe AST-based expression evaluator.
- calcapp/calculator.py: Calculator class that maintains history and memory (ans).
- calcapp/cli.py: Command-line interface (one-off and REPL modes).

Testing

Run tests with:

  pytest
