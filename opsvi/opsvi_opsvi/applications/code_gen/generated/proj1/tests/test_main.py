import os
import sys

# Add src directory to path
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_DIR)

import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run(
        [sys.executable, "main.py", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "CLI Tool" in result.stdout


def test_cli_basic_usage(tmp_path):
    """Test basic CLI usage."""
    output_file = tmp_path / "output.txt"
    result = subprocess.run(
        [sys.executable, "main.py", "test_input", "--output", str(output_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_file.exists()
    assert "Processed: test_input" in output_file.read_text()
