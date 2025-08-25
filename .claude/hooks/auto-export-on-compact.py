#!/usr/bin/env python3
"""
Auto-export hook for /compact command
Saves the full session before compaction occurs
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def find_current_session():
    """Find the current Claude session file"""
    sessions_dir = Path.home() / ".claude" / "projects"

    if not sessions_dir.exists():
        return None

    # Get most recent JSONL file
    session_files = list(sessions_dir.glob("**/*.jsonl"))
    if not session_files:
        return None

    # Sort by modification time
    latest = max(session_files, key=lambda f: f.stat().st_mtime)
    return latest


def export_session():
    """Export the current session before compaction"""

    # Configuration
    export_base = Path.home() / ".claude" / "session-exports" / "pre-compact"
    export_base.mkdir(parents=True, exist_ok=True)

    # Find current session
    current_session = find_current_session()
    if not current_session:
        print("⚠️  No active session found to export", file=sys.stderr)
        return False

    # Generate export filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = Path.cwd().name
    export_name = f"{project_name}_{timestamp}.jsonl"
    export_path = export_base / export_name

    # Also create a metadata file
    metadata_path = export_base / f"{project_name}_{timestamp}_metadata.json"

    try:
        # Copy the session file
        shutil.copy2(current_session, export_path)

        # Create metadata
        metadata = {
            "exported_at": datetime.now().isoformat(),
            "original_file": str(current_session),
            "project_path": str(Path.cwd()),
            "file_size": export_path.stat().st_size,
            "line_count": sum(1 for _ in open(export_path)),
            "reason": "pre-compact-auto-export",
            "session_duration": None,  # Could calculate from first/last message
        }

        # Try to get session info
        with open(export_path) as f:
            lines = f.readlines()
            if lines:
                first_msg = json.loads(lines[0])
                last_msg = json.loads(lines[-1])

                # Extract timestamps if available
                if "timestamp" in first_msg and "timestamp" in last_msg:
                    metadata["session_start"] = first_msg["timestamp"]
                    metadata["session_end"] = last_msg["timestamp"]

        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Report success
        size_mb = export_path.stat().st_size / (1024 * 1024)
        print(f"✅ Session auto-exported before compact:", file=sys.stderr)
        print(f"   📄 Session: {export_path} ({size_mb:.2f} MB)", file=sys.stderr)
        print(f"   📊 Metadata: {metadata_path}", file=sys.stderr)

        # Also create a symlink to "latest"
        latest_link = export_base / "latest.jsonl"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(export_path)

        return True

    except Exception as e:
        print(f"❌ Failed to export session: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    # This runs as a hook before /compact
    success = export_session()

    # Always exit 0 to allow compact to proceed
    # Even if export fails, we don't want to block compaction
    sys.exit(0)
