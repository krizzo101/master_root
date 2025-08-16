import os
import sys
import tempfile
from io import StringIO

import networkx as nx

from ..main import main


def run_cli(args):
    # Save original sys.argv and sys.stdout
    orig_argv = sys.argv
    orig_stdout = sys.stdout
    sys.argv = ["main.py"] + args
    sys.stdout = StringIO()
    try:
        main()
        output = sys.stdout.getvalue()
        return output
    finally:
        sys.argv = orig_argv
        sys.stdout = orig_stdout


def test_cli_valid_csv():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("A,B\nB,C\n")
        f.flush()
        result = run_cli(["--csv", f.name, "--source", "A", "--target", "C"])
    os.unlink(f.name)
    assert "Shortest path: ['A', 'B', 'C']" in result
    assert "LLM-augmented answer" in result


def test_cli_missing_args():
    result = run_cli([])
    assert "provide a graph file" in result


def test_cli_invalid_file():
    try:
        result = run_cli(["--csv", "nonexistent.csv", "--source", "A", "--target", "B"])
        # If no exception, check for error message in output
        assert "No such file or directory" in result or "No such file" in result
    except FileNotFoundError:
        pass  # Expected


def test_cli_disconnected_nodes():
    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            f.write("A,B\nC,D\n")
            f.flush()
            result = run_cli(["--csv", f.name, "--source", "A", "--target", "D"])
        os.unlink(f.name)
        # If no exception, check for error message in output
        assert "No path" in result or "NetworkXNoPath" in result
    except nx.NetworkXNoPath:
        pass  # Expected
