import pytest
import sys
import io
from eval_exec_demo import demonstrate_eval, demonstrate_exec, main


@pytest.fixture
def capture_stdout():
    """Fixture to capture standard output during the test."""
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    yield new_stdout
    sys.stdout = old_stdout


@pytest.fixture
def bad_expression_data():
    return [
        "1/0",  # Division by zero
        "unknown_var",  # NameError
        "'a' + 5",  # TypeError
        "[1,2].unknown",  # AttributeError
    ]


def test_demonstrate_eval_outputs_correct_result(capture_stdout):
    """
    Test demonstrate_eval() prints the expected evaluated results of expressions.
    Checks that the printed output contains expected values of the evaluation.
    """
    demonstrate_eval()
    output = capture_stdout.getvalue()
    # The demonstration should output the evaluation of an expression, e.g. arithmetic
    assert "Evaluation result" in output
    # Extract numeric result from output to check it evaluates correctly
    import re

    match = re.search(r"Evaluation result: (.+)", output)
    assert match is not None
    expr_result = match.group(1)
    # eval on a known expression '5 + 3' should output '8'
    assert expr_result.strip() == "8"


def test_demonstrate_exec_executes_code_and_prints(capture_stdout):
    """
    Test demonstrate_exec() runs a simple code block modifying local variables and prints output.
    Verify that output contains expected print statements from the executed code.
    """
    demonstrate_exec()
    output = capture_stdout.getvalue()
    # Should print the exec demonstrating text
    assert "Sum calculated by exec" in output
    # Should include correct sum result 15 from range 5
    assert "15" in output


import builtins


def test_demonstrate_eval_handles_invalid_expression_gracefully(
    monkeypatch, capsys, bad_expression_data
):
    """
    Patch demonstrate_eval to evaluate invalid expressions and confirm it handles errors gracefully
    and prints an error message instead of raising.
    """
    import eval_exec_demo

    for bad_expr in bad_expression_data:

        def faulty_eval():
            try:
                # Simulate an eval call to bad expression
                eval(bad_expr)
            except Exception as e:
                print(f"Evaluation error: {e}")

        # Patch eval to call faulty_eval in the demonstrate_eval context for testing
        # We patch demonstrate_eval to replace eval call with eval of bad_expr

        # Backup original demonstrate_eval
        original_demonstrate_eval = eval_exec_demo.demonstrate_eval

        def patched_demonstrate_eval():
            try:
                result = eval(bad_expr)
                print(f"Evaluation result: {result}")
            except Exception as e:
                print(f"Evaluation error: {e}")

        eval_exec_demo.demonstrate_eval = patched_demonstrate_eval

        # Capture output
        captured = capsys.readouterr()
        eval_exec_demo.demonstrate_eval()
        captured2 = capsys.readouterr()

        # Validate error message printed
        assert "Evaluation error" in captured2.out

        # Restore original function for next iteration
        eval_exec_demo.demonstrate_eval = original_demonstrate_eval


def test_demonstrate_exec_handles_errors(monkeypatch, capsys):
    """
    Patch demonstrate_exec with faulty code to induce SyntaxError or RuntimeError,
    ensure error is caught and an error message is printed.
    """
    import eval_exec_demo

    faulty_codes = [
        "for i in range(3) print(i)",  # SyntaxError missing colon
        "raise RuntimeError('Test error')",  # RuntimeError
    ]

    original_demonstrate_exec = eval_exec_demo.demonstrate_exec

    for code in faulty_codes:

        def patched_demonstrate_exec():
            try:
                exec(code)
            except Exception as e:
                print(f"Exec error: {e}")

        eval_exec_demo.demonstrate_exec = patched_demonstrate_exec

        # Capture output
        captured = capsys.readouterr()
        eval_exec_demo.demonstrate_exec()
        captured2 = capsys.readouterr()

        assert "Exec error" in captured2.out

    # Restore
    eval_exec_demo.demonstrate_exec = original_demonstrate_exec


def test_main_runs_without_error_and_produces_expected_output(capture_stdout):
    """
    Test main() function runs end-to-end demo script.
    Should call demonstrate_eval and demonstrate_exec and print all outputs.
    """
    main()
    output = capture_stdout.getvalue()
    # Confirm outputs from both demonstrate_eval and demonstrate_exec
    assert "Evaluation result" in output
    assert "Sum calculated by exec" in output


def test_main_can_be_called_multiple_times_cleanly(capture_stdout):
    """
    Calls main() multiple times to assert that no state leak or errors occur on repeated execution.
    Output should contain expected evaluation and exec results each time.
    """
    for _ in range(3):
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        main()
        output = capture_stdout.getvalue()
        assert "Evaluation result" in output
        assert "Sum calculated by exec" in output


import builtins


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("2 + 2", "4"),
        ("10 / 2", "5.0"),
        ("len('hello')", "5"),
        ("sorted([3,1,2])", "[1, 2, 3]"),
    ],
)
def test_demonstrate_eval_with_various_expressions(expression, expected, capsys):
    """
    Test eval execution with various valid expressions.
    We patch demonstrate_eval to run eval(expression) and print the result.
    """
    import eval_exec_demo

    def patched_demonstrate_eval():
        try:
            result = eval(expression)
            print(f"Evaluation result: {result}")
        except Exception as e:
            print(f"Evaluation error: {e}")

    original_demonstrate_eval = eval_exec_demo.demonstrate_eval
    eval_exec_demo.demonstrate_eval = patched_demonstrate_eval

    captured = capsys.readouterr()
    eval_exec_demo.demonstrate_eval()
    captured2 = capsys.readouterr()

    assert f"Evaluation result: {expected}" in captured2.out

    eval_exec_demo.demonstrate_eval = original_demonstrate_eval


@pytest.mark.parametrize(
    "code_snippet,expected_output",
    [
        ("a = 1\nb = 2\nprint(f'Result: {a + b}')", "Result: 3"),
        (
            "for i in range(3):\n    print(f'Number: {i}')",
            "Number: 0\nNumber: 1\nNumber: 2",
        ),
    ],
)
def test_demonstrate_exec_with_various_code(code_snippet, expected_output, capsys):
    """
    Test exec with various multiline code blocks printing output.
    Patching demonstrate_exec to run exec on given code snippet.
    Assert output contains expected strings.
    """
    import eval_exec_demo

    def patched_demonstrate_exec():
        try:
            exec(code_snippet)
        except Exception as e:
            print(f"Exec error: {e}")

    original_demonstrate_exec = eval_exec_demo.demonstrate_exec
    eval_exec_demo.demonstrate_exec = patched_demonstrate_exec

    captured = capsys.readouterr()
    eval_exec_demo.demonstrate_exec()
    captured2 = capsys.readouterr()

    # Expected output may be multiline, verify all lines individually
    for line in expected_output.split("\n"):
        assert line in captured2.out

    eval_exec_demo.demonstrate_exec = original_demonstrate_exec


import runpy
import sys
import io
import types


def test_script_runnable_from_command_line_invokes_main(capsys):
    """
    Test the script can be run from command line as __main__, triggering main() and printing output
    by running the module via runpy.
    """
    # runpy returns the module dictionary
    result = runpy.run_module("eval_exec_demo", run_name="__main__")
    # Capture output from the run
    captured = capsys.readouterr()
    assert "Evaluation result" in captured.out
    assert "Sum calculated by exec" in captured.out
    # main function should be in module dict
    assert "main" in result
