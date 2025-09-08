#!/usr/bin/env python3
"""
Debug Agent Monitor - Shows exactly what's happening
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path


async def debug_discovery():
    """Debug file discovery process"""
    projects_dir = Path.home() / ".claude" / "projects"
    pattern = "*"

    print(f"🔍 DEBUG: Projects directory: {projects_dir}")
    print(f"🔍 DEBUG: Pattern: {pattern}")
    print(f"🔍 DEBUG: Directory exists: {projects_dir.exists()}")

    if not projects_dir.exists():
        print("❌ Projects directory doesn't exist!")
        return []

    print(f"\n📁 All subdirectories:")
    subdirs = list(projects_dir.glob(pattern))
    for i, subdir in enumerate(subdirs[:10]):  # Show first 10
        print(f"  {i+1}. {subdir.name}")
    print(f"  ... ({len(subdirs)} total)")

    print(f"\n📄 Looking for .jsonl files...")
    cutoff_time = time.time() - 86400  # 24 hours
    agent_files = []

    for project_dir in subdirs:
        if not project_dir.is_dir():
            continue

        jsonl_files = list(project_dir.glob("*.jsonl"))
        if jsonl_files:
            print(f"\n📂 {project_dir.name}:")
            for jsonl_file in jsonl_files:
                try:
                    stat = jsonl_file.stat()
                    age_hours = (time.time() - stat.st_mtime) / 3600
                    size = stat.st_size

                    if size > 0 and stat.st_mtime > cutoff_time:
                        agent_files.append(jsonl_file)
                        print(
                            f"  ✅ {jsonl_file.name} ({size} bytes, {age_hours:.1f}h old)"
                        )
                    else:
                        print(
                            f"  ❌ {jsonl_file.name} ({size} bytes, {age_hours:.1f}h old) - SKIPPED"
                        )
                except OSError as e:
                    print(f"  ❌ {jsonl_file.name} - ERROR: {e}")

    print(f"\n🎯 FOUND {len(agent_files)} active agent files")
    return agent_files


async def debug_file_reading(agent_files):
    """Debug file reading process"""
    if not agent_files:
        print("❌ No files to read!")
        return

    # Test reading first file
    test_file = agent_files[0]
    agent_id = test_file.stem[-8:]

    print(f"\n📖 Testing file reading: {test_file.name}")
    print(f"🆔 Agent ID: {agent_id}")

    try:
        with open(test_file, "r", encoding="utf-8") as f:
            # Read last few lines
            lines = f.readlines()
            total_lines = len(lines)
            print(f"📊 Total lines: {total_lines}")

            if total_lines > 0:
                print(f"\n📝 Last few entries:")
                for i, line in enumerate(lines[-3:], total_lines - 2):
                    if line.strip():
                        try:
                            entry = json.loads(line.strip())
                            timestamp = entry.get("timestamp", "no timestamp")
                            role = entry.get("role", "unknown")
                            content_type = type(entry.get("content", "unknown"))
                            print(
                                f"  {i}. [{timestamp}] {role} ({content_type.__name__})"
                            )
                        except json.JSONDecodeError:
                            print(f"  {i}. [INVALID JSON] {line[:50]}...")
            else:
                print("📝 File is empty!")

    except Exception as e:
        print(f"❌ Error reading file: {e}")


async def debug_log_processing(agent_files):
    """Debug log entry processing"""
    if not agent_files:
        return

    test_file = agent_files[0]
    agent_id = test_file.stem[-8:]

    print(f"\n🔄 Testing log entry processing...")

    try:
        with open(test_file, "r") as f:
            lines = f.readlines()
            if lines:
                # Process last line
                last_line = lines[-1].strip()
                if last_line:
                    try:
                        entry = json.loads(last_line)

                        # Extract key info
                        timestamp = entry.get("timestamp", "")
                        role = entry.get("role", "unknown")
                        content = entry.get("content", [])

                        print(f"📅 Timestamp: {timestamp}")
                        print(f"👤 Role: {role}")
                        print(f"📝 Content type: {type(content).__name__}")

                        if isinstance(content, list):
                            print(f"📝 Content items: {len(content)}")
                            for i, item in enumerate(content):
                                if isinstance(item, dict):
                                    item_type = item.get("type", "unknown")
                                    print(f"  {i+1}. Type: {item_type}")
                                    if item_type == "tool_use":
                                        tool_name = item.get("name", "unknown")
                                        print(f"     Tool: {tool_name}")

                        # Try formatting
                        if timestamp and "T" in timestamp:
                            try:
                                dt = datetime.fromisoformat(
                                    timestamp.replace("Z", "+00:00")
                                )
                                time_str = dt.strftime("%H:%M:%S")
                                print(f"🕐 Formatted time: {time_str}")
                            except ValueError as e:
                                print(f"❌ Time parsing error: {e}")

                        print(f"✅ Entry processing successful!")

                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing error: {e}")
                        print(f"Raw line: {last_line[:100]}...")
    except Exception as e:
        print(f"❌ Processing error: {e}")


async def main():
    print("🚀 AGENT MONITOR DEBUG SESSION")
    print("=" * 50)

    # Test file discovery
    agent_files = await debug_discovery()

    # Test file reading
    await debug_file_reading(agent_files)

    # Test log processing
    await debug_log_processing(agent_files)

    print("\n" + "=" * 50)
    print("🏁 DEBUG SESSION COMPLETE")

    if agent_files:
        print(f"✅ Found {len(agent_files)} active files")
        print("📋 Files found:")
        for i, f in enumerate(agent_files[:5], 1):
            print(f"  {i}. {f.name} ({f.parent.name})")
        if len(agent_files) > 5:
            print(f"  ... and {len(agent_files) - 5} more")
    else:
        print("❌ No active agent files found!")
        print("💡 Possible issues:")
        print("  - No recent .jsonl files (last 24h)")
        print("  - All files are empty")
        print("  - Permission issues")
        print("  - Wrong directory pattern")


if __name__ == "__main__":
    asyncio.run(main())
