#!/usr/bin/env python3
"""
Project Information Collector

This script runs the bootstrap project inspector to collect comprehensive
information about the ACCF project and generate a knowledge.json file.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run the project inspector from the bootstrap directory"""

    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    bootstrap_dir = project_root / ".bootstrap"

    if not bootstrap_dir.exists():
        print("❌ Bootstrap directory not found!")
        print(f"Expected location: {bootstrap_dir}")
        sys.exit(1)

    # Change to bootstrap directory and run the inspector
    os.chdir(bootstrap_dir)

    print("🔍 Running ACCF Project Inspector...")
    print(f"📁 Project root: {project_root}")
    print(f"📂 Bootstrap dir: {bootstrap_dir}")
    print()

    try:
        # Run the inspector script
        result = subprocess.run(
            [sys.executable, "run_inspector.py"],
            capture_output=True,
            text=True,
            check=True,
        )

        print(result.stdout)

        # Check if knowledge.json was created
        knowledge_file = bootstrap_dir / "knowledge.json"
        if knowledge_file.exists():
            size = knowledge_file.stat().st_size
            print(f"\n✅ Success! Knowledge file created: {knowledge_file}")
            print(f"📊 File size: {size:,} bytes")

            # Move to project root for easier access
            root_knowledge = project_root / "knowledge.json"
            if root_knowledge.exists():
                root_knowledge.unlink()  # Remove if exists
            knowledge_file.rename(root_knowledge)
            print(f"📋 Moved to: {root_knowledge}")

        else:
            print("❌ Knowledge file was not created!")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running inspector: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
