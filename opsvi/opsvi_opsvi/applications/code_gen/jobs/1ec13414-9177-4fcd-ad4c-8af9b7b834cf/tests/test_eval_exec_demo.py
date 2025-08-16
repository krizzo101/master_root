"""
Unit tests for eval_exec_demo.py

These tests confirm that the demonstration functions output the expected results.
No user input or dynamic code evaluation is performed.
"""

import subprocess
import sys
from typing import Tuple

import io
import contextlib
import eval_exec_demo


def run_main_and_capture_output() -> Tuple[str, str]:
    """
    Runs the main() function from eval_exec_demo and captures stdout and stderr.
    Returns:
        Tuple containing stdout and stderr outputs.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        eval_exec_demo.main()
    return stdout.getvalue(), stderr.getvalue()


def test_eval_output():
    stdout, _ = run_main_and_capture_output()
    assert "[eval()] The result of the expression '2 + 3 * (4 - 1)' is: 11" in stdout
    assert (
        "[eval()] The result of the expression 'pow(x, 2) + y' with x=5, y=8 is: 33"
        in stdout
    )


def test_exec_output():
    stdout, _ = run_main_and_capture_output()
    assert "[exec()] After executing code, z = 12" in stdout
    assert "[exec()] Function greet executed: Hello, Alice!" in stdout


def test_script_runs_without_error():
    # Run as a subprocess to check exit code is 0
    result = subprocess.run(
        [sys.executable, "eval_exec_demo.py"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "[eval()]" in result.stdout
    assert "[exec()]" in result.stdout
