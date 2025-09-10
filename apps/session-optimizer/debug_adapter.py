#!/usr/bin/env python3
"""
Debug the ClaudeFormatAdapter to identify specific issues
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from claude_format_adapter import AdapterConfig, ClaudeFormatAdapter


def debug_adapter_issues():
    """Debug specific issues with the adapter"""

    # Find a sample file that's failing
    claude_projects = Path("/home/opsvi/.claude/projects")
    sample_file = next(claude_projects.glob("**/*.jsonl"))

    print(f"🔍 Debugging file: {sample_file.name}")

    adapter = ClaudeFormatAdapter(AdapterConfig(preserve_all_metadata=True))

    try:
        print("\n📊 Attempting conversion...")
        converted_session = adapter.convert_session_file(sample_file)

        print(f"✅ Conversion successful!")
        print(f"   Session ID: {converted_session.get('session_id', 'MISSING')}")
        print(f"   Messages: {len(converted_session.get('messages', []))}")
        print(f"   Conversion stats: {converted_session.get('conversion_stats', {})}")

        # Check message structure
        messages = converted_session.get("messages", [])
        if messages:
            print(f"\n📝 Sample message structure:")
            sample_msg = messages[0]
            print(f"   Keys: {list(sample_msg.keys())}")
            print(f"   Type: {sample_msg.get('type')}")
            print(f"   Has content: {'content' in sample_msg}")
            print(f"   Has tool_calls: {'tool_calls' in sample_msg}")

        return True

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback

        traceback.print_exc()

        # Try to read a few lines manually to see the structure
        print(f"\n🔬 Manual inspection of first 3 lines:")
        try:
            with open(sample_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 3:
                        break
                    if line.strip():
                        try:
                            record = json.loads(line)
                            print(
                                f"   Line {i+1}: type={record.get('type')}, keys={list(record.keys())[:5]}"
                            )

                            # Check for specific Claude structure
                            if "message" in record:
                                msg = record["message"]
                                print(
                                    f"      message keys: {list(msg.keys()) if isinstance(msg, dict) else type(msg)}"
                                )
                        except json.JSONDecodeError as je:
                            print(f"   Line {i+1}: JSON decode error - {je}")
        except Exception as re:
            print(f"   File read error: {re}")

        return False


def test_datetime_parsing():
    """Test the timestamp parsing which might be causing issues"""
    from claude_format_adapter import ClaudeFormatAdapter

    adapter = ClaudeFormatAdapter()

    # Test various timestamp formats found in Claude files
    timestamps = [
        "2025-09-07T10:35:50.413Z",
        "2025-09-07T10:35:53.126Z",
        "2025-09-09T04:25:35.126Z",
        None,
        "",
        "invalid-timestamp",
    ]

    print("\n🕐 Testing timestamp parsing:")
    for ts in timestamps:
        try:
            parsed = adapter._parse_timestamp(ts)
            print(f"   '{ts}' -> {parsed}")
        except Exception as e:
            print(f"   '{ts}' -> ERROR: {e}")


if __name__ == "__main__":
    print("🔧 Debugging Claude Format Adapter")
    print("=" * 40)

    success = debug_adapter_issues()
    test_datetime_parsing()

    if not success:
        print("\n💡 Possible fixes needed:")
        print("   1. Fix timestamp parsing issues")
        print("   2. Handle missing 'message' field")
        print("   3. Improve error handling for malformed records")
        print("   4. Handle different Claude file formats")
