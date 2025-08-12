#!/usr/bin/env python3
"""
Simple recursive Claude Code task demonstration.
Uses the MCP wrapper to spawn a child task that analyzes the Python environment.
"""

import subprocess


def run_recursive_task():
    """Run a recursive Claude Code task using the MCP wrapper."""

    print("=" * 60)
    print("RECURSIVE CLAUDE CODE DEMONSTRATION")
    print("=" * 60)

    # The task for the child Claude instance
    task = """
    Execute the following Python analysis commands and report results:
    1. Run: python -c "import sys; print(f'Python: {sys.version}')"
    2. Run: python -c "import sys; print(f'Executable: {sys.executable}')"
    3. Run: pip list | head -20
    4. Check if these packages are installed: openai, anthropic, langchain, fastmcp
    5. Print the current working directory
    
    Provide a brief summary of the environment.
    """

    print("\nTask for child Claude instance:")
    print(task)
    print("\n" + "-" * 60)

    # Use the claude command directly with recursion
    cmd = [
        "claude",
        "run",
        "--permission-mode",
        "bypassPermissions",
        "--output-format",
        "text",
        task,
    ]

    print("\nSpawning child Claude Code instance...")
    print(f"Command: {' '.join(cmd)}")
    print("\n" + "-" * 60)

    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/opsvi/master_root",
        )

        print("\nCHILD INSTANCE OUTPUT:")
        print("=" * 60)

        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error (return code {result.returncode}):")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("\n⚠️ Child instance timed out after 60 seconds")
    except Exception as e:
        print(f"\n❌ Error spawning child instance: {e}")

    print("\n" + "=" * 60)
    print("✅ Recursive task demonstration complete")


if __name__ == "__main__":
    run_recursive_task()
