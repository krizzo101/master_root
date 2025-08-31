#!/usr/bin/env python3
"""
Find current Claude session by writing a unique marker and searching for it
"""

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path


def generate_unique_marker():
    """Generate a unique marker that won't appear naturally"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_id = uuid.uuid4().hex[:16]
    return f"CLAUDE_SESSION_BEACON_{timestamp}_{unique_id}"


def write_marker_to_chat(marker):
    """Write marker that will appear in the session log"""
    # Multiple formats to increase chances of capture
    print(f"\n<!-- SESSION_MARKER: {marker} -->\n", flush=True)
    return marker


def search_for_marker_in_sessions(marker, base_dir=None, max_wait=5):
    """
    Search for the marker in session files
    """
    if not base_dir:
        base_dir = Path.home() / ".claude" / "projects"

    if not base_dir.exists():
        return None

    found_session = None
    start_time = time.time()

    # Try multiple times with short waits
    attempts = 0
    while time.time() - start_time < max_wait and not found_session:
        attempts += 1

        # Find all jsonl files modified in the last hour
        recent_files = []
        for jsonl_file in base_dir.rglob("*.jsonl"):
            try:
                mtime = jsonl_file.stat().st_mtime
                if time.time() - mtime < 3600:  # Modified in last hour
                    recent_files.append(jsonl_file)
            except:
                continue

        # Search for marker in recent files
        for session_file in recent_files:
            try:
                # Use grep for efficiency
                result = subprocess.run(
                    ["grep", "-l", marker, str(session_file)],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )

                if result.returncode == 0:
                    found_session = session_file
                    break

            except subprocess.TimeoutExpired:
                # Fallback to Python search
                try:
                    with open(session_file, "r") as f:
                        # Read in chunks from the end (most recent entries)
                        f.seek(0, 2)  # Go to end
                        file_size = f.tell()

                        # Read last 100KB
                        chunk_size = min(102400, file_size)
                        f.seek(max(0, file_size - chunk_size))
                        content = f.read()

                        if marker in content:
                            found_session = session_file
                            break
                except:
                    continue

        if not found_session and attempts < 3:
            time.sleep(1)  # Wait a bit for the log to be written

    return found_session


def get_session_uuid_from_path(session_path):
    """Extract UUID from session file path"""
    if session_path:
        return session_path.stem  # filename without .jsonl
    return None


def identify_current_session():
    """
    Main function to identify current session
    Returns: (uuid, file_path, confidence)
    """

    # Check if we're in a Claude Code environment
    if not os.getenv("CLAUDE_PROJECT_ROOT"):
        return None, None, 0.0

    # Generate and write marker
    marker = generate_unique_marker()
    write_marker_to_chat(marker)

    # Search for the marker
    session_file = search_for_marker_in_sessions(marker)

    if session_file:
        uuid = get_session_uuid_from_path(session_file)
        return uuid, str(session_file), 0.95

    # Fallback: Find most recently modified session for current project
    project_root = Path(os.getenv("CLAUDE_PROJECT_ROOT", os.getcwd()))
    project_name = project_root.name
    base_dir = Path.home() / ".claude" / "projects"

    most_recent = None
    most_recent_time = 0

    for project_dir in base_dir.glob(f"*{project_name}*"):
        for session_file in project_dir.glob("*.jsonl"):
            try:
                mtime = session_file.stat().st_mtime
                if (
                    time.time() - mtime < 600 and mtime > most_recent_time
                ):  # Last 10 minutes
                    most_recent = session_file
                    most_recent_time = mtime
            except:
                continue

    if most_recent:
        uuid = get_session_uuid_from_path(most_recent)
        return uuid, str(most_recent), 0.7

    return None, None, 0.0


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Find current Claude session")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--save", action="store_true", help="Save to state file for other tools"
    )

    args = parser.parse_args()

    print("Identifying current Claude session...", file=sys.stderr)
    uuid, file_path, confidence = identify_current_session()

    if args.save and uuid:
        # Save to state file
        state_file = (
            Path.home() / ".claude" / "session_manager" / "current_session.json"
        )
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "session_id": uuid,
            "file_path": file_path,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "project": os.getenv("CLAUDE_PROJECT_ROOT", "unknown"),
        }

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        print(f"Saved session info to {state_file}", file=sys.stderr)

    if args.json:
        result = {
            "session_id": uuid,
            "file_path": file_path,
            "confidence": confidence,
            "found": uuid is not None,
        }
        print(json.dumps(result, indent=2))
    else:
        if uuid:
            print(f"Session UUID: {uuid}")
            print(f"File: {file_path}")
            print(f"Confidence: {confidence:.0%}")
        else:
            print("Could not identify current session")
            print("This is normal if not running in an active Claude Code session")

    return 0 if uuid else 1


if __name__ == "__main__":
    sys.exit(main())
