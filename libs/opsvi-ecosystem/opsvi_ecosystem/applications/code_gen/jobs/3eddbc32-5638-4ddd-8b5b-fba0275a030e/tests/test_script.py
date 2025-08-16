import os
import sys

# Add src directory to path
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_DIR)

import sys

import script


def test_main_output(capsys):
    """Test main function output."""
    script.main()
    captured = capsys.readouterr()
    assert "Hello from the generated script!" in captured.out
    assert "The answer is: 42" in captured.out
