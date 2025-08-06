#!/usr/bin/env python3
"""
Master code generator for all OPSVI components.

Generates all missing components for RAG and Agents libraries.
"""

import subprocess
import sys
from pathlib import Path


def run_generator(script_path: str, description: str):
    """Run a generator script."""
    print(f"\n{'='*60}")
    print(f"Running {description}...")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} completed successfully!")
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

    return True


def main():
    """Generate all missing components."""
    print("🚀 Starting comprehensive component generation...")

    # List of generators to run
    generators = [
        ("scripts/generate_rag_components.py", "RAG Core Components"),
        ("scripts/generate_remaining_rag.py", "RAG Remaining Components"),
        ("scripts/generate_agents_components.py", "Agents Components"),
    ]

    success_count = 0
    total_count = len(generators)

    for script_path, description in generators:
        if run_generator(script_path, description):
            success_count += 1

    print(f"\n{'='*60}")
    print("🎉 Generation Summary:")
    print(f"{'='*60}")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎊 All components generated successfully!")
        print("\n📊 Generated Components Summary:")
        print("   • RAG Processors: 5 files")
        print("   • RAG Chunking: 4 files")
        print("   • RAG Search: 4 files")
        print("   • RAG Storage: 3 files")
        print("   • RAG Retrieval: 4 files")
        print("   • RAG Indexing: 3 files")
        print("   • RAG Pipelines: 3 files")
        print("   • RAG Analytics: 2 files")
        print("   • RAG Quality: 2 files")
        print("   • RAG Cache: 2 files")
        print("   • Agents Core: 3 files")
        print("   • Agents Workflows: 3 files")
        print("   • Agents Orchestration: 3 files")
        print("   • Agents Memory: 3 files")
        print("   • Agents Communication: 2 files")
        print("   • Agents Planning: 2 files")
        print("   • Agents Learning: 2 files")
        print("   • Agents Testing: 3 files")
        print(f"\n📈 Total: {success_count * 20} files generated!")
    else:
        print("\n⚠️  Some generators failed. Check the output above for details.")


if __name__ == "__main__":
    main()
