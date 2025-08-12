#!/usr/bin/env python3
"""
Test script to verify file writing functionality in Smart Decomposition

This script tests the new file writing pattern based on old OAMAT.
"""

import asyncio
from pathlib import Path
import sys

# Add the src directory to path for local imports
app_src_root = Path(__file__).parent / "src"
sys.path.insert(0, str(app_src_root))

from src.applications.oamat_sd.src.smart_decomposition_agent import (
    SmartDecompositionAgent,
)


async def test_file_writing():
    """Test the file writing functionality"""
    print("🧪 Testing Smart Decomposition File Writing...")

    # Create agent
    agent = SmartDecompositionAgent()

    # Test with a simple request that should generate files
    test_request = "Create a simple Python hello world program with documentation"

    print(f"📝 Testing request: {test_request}")
    print("🔄 Processing...")

    try:
        result = await agent.process_request(test_request)

        print("\n" + "=" * 80)
        print("🔍 TEST RESULTS")
        print("=" * 80)

        if result["success"]:
            print("✅ SUCCESS: Agent execution completed")

            # Check if project was created
            if result.get("project_path"):
                project_path = Path(result["project_path"])
                print(f"📁 Project created at: {project_path}")

                if project_path.exists():
                    print("✅ Project directory exists")

                    # List generated files
                    files = list(project_path.rglob("*"))
                    file_count = len([f for f in files if f.is_file()])

                    if file_count > 0:
                        print(f"✅ {file_count} files generated:")
                        for file_path in files:
                            if file_path.is_file():
                                relative_path = file_path.relative_to(project_path)
                                size = file_path.stat().st_size
                                print(f"  📄 {relative_path} ({size} bytes)")

                                # Show first few lines of small files
                                if size < 1000:
                                    try:
                                        with open(file_path, encoding="utf-8") as f:
                                            first_lines = f.read(200)
                                        print(f"      Preview: {first_lines[:100]}...")
                                    except Exception as e:
                                        print(f"      Could not preview: {e}")
                    else:
                        print("⚠️ No files were generated")
                else:
                    print("❌ Project directory was not created")
            else:
                print("❌ No project path in result")

        else:
            print("❌ FAILED: Agent execution failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get("errors"):
                print("Additional errors:")
                for error in result["errors"]:
                    print(f"  - {error}")

    except Exception as e:
        print(f"❌ TEST FAILED with exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_file_writing())
