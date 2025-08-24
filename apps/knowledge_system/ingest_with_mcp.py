#!/usr/bin/env python3
"""
Direct ingestion using MCP knowledge tool (bypasses Neo4j auth issues)
"""

import asyncio
import json

# We'll call the MCP tool directly via subprocess
import subprocess
from pathlib import Path
from typing import Dict, List


def store_knowledge(content: str, knowledge_type: str, tags: List[str]) -> Dict:
    """Store knowledge using MCP tool"""

    # Prepare the command to call the MCP knowledge store
    cmd = [
        "/home/opsvi/miniconda/bin/python",
        "-c",
        f"""
import sys
sys.path.insert(0, "/home/opsvi/master_root")
from apps.knowledge_system.mcp_knowledge_server import store_knowledge_direct

result = store_knowledge_direct(
    content='''{content}''',
    knowledge_type='{knowledge_type}',
    tags={tags}
)
print(result)
""",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def ingest_reference_files(max_files: int = 30):
    """Ingest reference files"""

    reference_dir = Path("/home/opsvi/.reference")

    # Priority files to ingest
    priority_patterns = [
        "gpt-5*.txt",
        "responses*.txt",
        "**/README.md",
        "**/*example*.py",
    ]

    files = []
    for pattern in priority_patterns:
        for f in reference_dir.glob(pattern):
            if f.is_file() and f not in files:
                files.append(f)
                if len(files) >= max_files:
                    break

    print(f"Processing {len(files)} files...")

    success_count = 0
    for i, file_path in enumerate(files, 1):
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()[:2000]  # Limit size

            if len(content) < 100:
                continue

            # Determine type based on file
            if file_path.suffix == ".py":
                knowledge_type = "CODE_PATTERN"
            elif file_path.suffix == ".md":
                knowledge_type = "DOCUMENTATION"
            else:
                knowledge_type = "REFERENCE"

            # Generate tags
            tags = [
                file_path.stem.replace("-", "_").replace(".", "_")[:20],
                file_path.suffix[1:] if file_path.suffix else "text",
            ]

            # Add special tags
            if "gpt-5" in str(file_path).lower():
                tags.append("gpt5")
            if "responses" in str(file_path).lower():
                tags.append("responses_api")
            if "openai" in str(file_path).lower():
                tags.append("openai")

            # Store via MCP
            result = store_knowledge(content, knowledge_type, tags[:5])

            if result.get("success"):
                success_count += 1
                print(f"[{i}/{len(files)}] ✅ {file_path.name}")
            else:
                print(
                    f"[{i}/{len(files)}] ❌ {file_path.name}: {result.get('error', 'Unknown error')[:50]}"
                )

        except Exception as e:
            print(f"[{i}/{len(files)}] ❌ {file_path.name}: {str(e)[:50]}")

    print(f"\n{'='*60}")
    print(f"Ingestion complete: {success_count}/{len(files)} successful")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Use the actual MCP knowledge tool instead
    print("Using MCP knowledge tool for ingestion...")
    print("This bypasses Neo4j auth issues and stores directly")

    # Just demonstrate with a few files
    asyncio.run(ingest_reference_files(max_files=10))
