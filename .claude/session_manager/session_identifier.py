#!/usr/bin/env python3
"""
Claude Code Session Self-Identifier
Identifies current session by writing a unique marker and searching for it
"""

import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path


class SessionIdentifier:
    def __init__(self):
        self.project_root = os.getenv("CLAUDE_PROJECT_ROOT", os.getcwd())
        self.sessions_base = Path.home() / ".claude" / "projects"
        self.state_file = (
            Path.home() / ".claude" / "session_manager" / "identified_session.json"
        )
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def generate_marker(self):
        """Generate a unique marker for identification"""
        timestamp = int(time.time() * 1000000)  # Microsecond precision
        random_part = uuid.uuid4().hex[:8]
        marker = f"SESSION_MARKER_{timestamp}_{random_part}"
        return marker

    def write_marker(self, marker):
        """Write marker to stdout (will appear in chat log)"""
        # Write as a comment that won't affect the conversation
        print(f"<!-- {marker} -->", flush=True)
        return marker

    def search_for_marker(self, marker, wait_time=2):
        """Search for marker in session files"""
        # Wait a moment for the marker to be written to disk
        time.sleep(wait_time)

        # Search for the marker in all jsonl files
        found_sessions = []

        # Method 1: Use grep to search efficiently
        try:
            # Search in the sessions directory
            cmd = [
                "grep",
                "-l",
                marker,
                *[str(f) for f in self.sessions_base.rglob("*.jsonl")],
            ]

            # Limit to recent files (modified in last hour)
            recent_files = []
            for f in self.sessions_base.rglob("*.jsonl"):
                if f.exists():
                    mtime = f.stat().st_mtime
                    if time.time() - mtime < 3600:  # Last hour
                        recent_files.append(str(f))

            if recent_files:
                result = subprocess.run(
                    ["grep", "-l", marker] + recent_files,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            found_sessions.append(Path(line))
        except Exception as e:
            if os.getenv("DEBUG"):
                print(f"DEBUG: grep search failed: {e}")

        # Method 2: Python-based search as fallback
        if not found_sessions:
            for session_file in self.sessions_base.rglob("*.jsonl"):
                # Only check recent files
                if not session_file.exists():
                    continue

                mtime = session_file.stat().st_mtime
                if time.time() - mtime > 3600:  # Skip old files
                    continue

                try:
                    # Read last 1000 lines (recent activity)
                    with open(session_file, "r") as f:
                        lines = f.readlines()
                        recent_lines = lines[-1000:] if len(lines) > 1000 else lines

                        for line in recent_lines:
                            if marker in line:
                                found_sessions.append(session_file)
                                break
                except Exception:
                    continue

        return found_sessions

    def identify_session(self, write_marker_to_chat=True):
        """
        Identify current session using marker technique

        Args:
            write_marker_to_chat: If True, writes marker to stdout

        Returns:
            (session_id, session_file_path, confidence)
        """

        # Check if we have a recently identified session
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)

                # Check if identification is recent (within 5 minutes)
                identified_time = datetime.fromisoformat(state["timestamp"])
                if (datetime.now() - identified_time).seconds < 300:
                    session_file = Path(state["session_file"])
                    if session_file.exists():
                        return state["session_id"], session_file, state["confidence"]
            except Exception:
                pass

        # Generate and write marker
        marker = self.generate_marker()

        if write_marker_to_chat:
            self.write_marker(marker)

        # Search for the marker
        found_sessions = self.search_for_marker(marker)

        if found_sessions:
            # Use the first (or most recently modified) session
            session_file = found_sessions[0]
            session_id = session_file.stem  # filename without .jsonl

            # Save the identification
            state = {
                "session_id": session_id,
                "session_file": str(session_file),
                "marker": marker,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95,
                "project": self.project_root,
            }

            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)

            return session_id, session_file, 0.95

        return None, None, 0.0

    def quick_identify(self):
        """
        Quick identification without writing marker
        Uses most recently modified session for current project
        """
        project_name = Path(self.project_root).name
        pattern = f"*{project_name}*"

        most_recent = None
        most_recent_time = 0

        for project_dir in self.sessions_base.glob(pattern):
            for session_file in project_dir.glob("*.jsonl"):
                if session_file.exists():
                    mtime = session_file.stat().st_mtime
                    # Only consider files modified in last 10 minutes
                    if time.time() - mtime < 600 and mtime > most_recent_time:
                        most_recent = session_file
                        most_recent_time = mtime

        if most_recent:
            session_id = most_recent.stem
            return session_id, most_recent, 0.7

        return None, None, 0.0


def main():
    """CLI for session identification"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code Session Self-Identifier")
    parser.add_argument(
        "command", choices=["identify", "quick", "test"], help="Command to run"
    )
    parser.add_argument(
        "--no-marker", action="store_true", help="Don't write marker to chat"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    identifier = SessionIdentifier()

    if args.command == "identify":
        session_id, session_file, confidence = identifier.identify_session(
            write_marker_to_chat=not args.no_marker
        )

        if args.json:
            print(
                json.dumps(
                    {
                        "session_id": session_id,
                        "session_file": str(session_file) if session_file else None,
                        "confidence": confidence,
                    }
                )
            )
        else:
            if session_id:
                print(f"Session ID: {session_id}")
                print(f"File: {session_file}")
                print(f"Confidence: {confidence:.0%}")
            else:
                print("Could not identify session")

    elif args.command == "quick":
        session_id, session_file, confidence = identifier.quick_identify()

        if args.json:
            print(
                json.dumps(
                    {
                        "session_id": session_id,
                        "session_file": str(session_file) if session_file else None,
                        "confidence": confidence,
                    }
                )
            )
        else:
            if session_id:
                print(f"Session ID: {session_id}")
                print(f"File: {session_file}")
                print(f"Confidence: {confidence:.0%}")
            else:
                print("No recent session found")

    elif args.command == "test":
        print("Testing session identification...")
        print("1. Generating marker...")
        marker = identifier.generate_marker()
        print(f"   Marker: {marker}")

        print("2. Writing marker to chat...")
        identifier.write_marker(marker)

        print("3. Searching for marker...")
        found = identifier.search_for_marker(marker, wait_time=3)

        if found:
            print(f"   Found in: {found[0]}")
            print(f"   Session ID: {found[0].stem}")
            print("   SUCCESS!")
        else:
            print("   Not found - this is normal if not in active session")
            print("4. Trying quick identification...")
            session_id, session_file, confidence = identifier.quick_identify()
            if session_id:
                print(f"   Found recent session: {session_id}")
            else:
                print("   No recent sessions")


if __name__ == "__main__":
    main()
