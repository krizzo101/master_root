#!/usr/bin/env python3
"""
Claude Code Session Detector
Detects and tracks the current active session UUID
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


class SessionDetector:
    def __init__(self):
        self.project_root = os.getenv("CLAUDE_PROJECT_ROOT", os.getcwd())
        self.project_name = Path(self.project_root).name
        self.session_dir = Path.home() / ".claude" / "projects"
        self.state_file = (
            Path.home() / ".claude" / "session_manager" / "active_session.json"
        )
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def get_current_session_id(self):
        """
        Detect current session ID using multiple methods
        Returns: (session_id, method, confidence)
        """

        # Method 1: Check if passed via stdin (for hooks)
        if not sys.stdin.isatty():
            try:
                import select

                readable, _, _ = select.select([sys.stdin], [], [], 0.1)
                if readable:
                    data = json.load(sys.stdin)
                    if "session_id" in data:
                        return data["session_id"], "stdin", 1.0
                    if "sessionId" in data:
                        return data["sessionId"], "stdin", 1.0
            except:
                pass

        # Method 2: Check environment variable
        if "CLAUDE_SESSION_UUID" in os.environ:
            return os.environ["CLAUDE_SESSION_UUID"], "environment", 1.0

        # Method 3: Try marker-based self-identification
        try:
            from session_identifier import SessionIdentifier

            identifier = SessionIdentifier()

            # First try quick identification (no marker)
            session_id, session_file, confidence = identifier.quick_identify()
            if session_id and confidence > 0.6:
                self._save_state(session_id)
                return session_id, "self_identified", confidence
        except ImportError:
            pass

        # Method 4: Check saved state
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                    if "session_id" in state:
                        # Check if still active (modified in last 10 minutes)
                        session_file = self._find_session_file(state["session_id"])
                        if session_file and self._is_recently_modified(
                            session_file, minutes=10
                        ):
                            return state["session_id"], "state_file", 0.8
            except:
                pass

        # Method 5: Find most recently modified session file
        session_file = self._find_most_recent_session()
        if session_file:
            session_id = session_file.stem  # filename without .jsonl
            self._save_state(session_id)
            return session_id, "recent_file", 0.6

        # Method 6: Generate a deterministic session ID based on current context
        # This ensures consistency within the same Claude instance
        context_hash = self._generate_context_hash()
        return f"synthetic-{context_hash[:12]}", "synthetic", 0.3

    def _find_session_file(self, session_id):
        """Find session file by ID"""
        # Search in project-specific directories
        pattern = f"*{self.project_name}*"
        for project_dir in self.session_dir.glob(pattern):
            session_file = project_dir / f"{session_id}.jsonl"
            if session_file.exists():
                return session_file

        # Search in all directories
        for session_file in self.session_dir.rglob(f"{session_id}.jsonl"):
            return session_file

        return None

    def _find_most_recent_session(self):
        """Find the most recently modified session file for current project"""
        recent_file = None
        recent_time = datetime.min

        # Look for project-specific sessions
        pattern = f"*{self.project_name}*"
        for project_dir in self.session_dir.glob(pattern):
            for session_file in project_dir.glob("*.jsonl"):
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                if mtime > recent_time:
                    recent_time = mtime
                    recent_file = session_file

        # Only return if modified in last 30 minutes
        if recent_file and self._is_recently_modified(recent_file, minutes=30):
            return recent_file

        return None

    def _is_recently_modified(self, file_path, minutes=10):
        """Check if file was modified within the specified minutes"""
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(minutes=minutes)

    def _generate_context_hash(self):
        """Generate a hash based on current context"""
        context = {
            "project": self.project_root,
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "time": datetime.now().strftime("%Y%m%d%H"),  # Hour precision
        }
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()

    def _save_state(self, session_id):
        """Save current session ID to state file"""
        state = {
            "session_id": session_id,
            "project": self.project_root,
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_session_file_path(self, session_id=None):
        """Get the full path to session file"""
        if not session_id:
            session_id, _, _ = self.get_current_session_id()

        if session_id.startswith("synthetic-"):
            return None

        return self._find_session_file(session_id)

    def get_session_info(self, session_id=None):
        """Get detailed information about a session"""
        if not session_id:
            session_id, method, confidence = self.get_current_session_id()
        else:
            method = "provided"
            confidence = 1.0

        session_file = self.get_session_file_path(session_id)

        info = {
            "session_id": session_id,
            "detection_method": method,
            "confidence": confidence,
            "project": self.project_root,
            "exists": session_file is not None,
        }

        if session_file:
            stat = session_file.stat()
            info.update(
                {
                    "file_path": str(session_file),
                    "size_kb": stat.st_size / 1024,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "lines": sum(1 for _ in open(session_file)),
                }
            )

        return info


def main():
    """CLI interface for session detection"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code Session Detector")
    parser.add_argument(
        "command", choices=["current", "info", "path"], help="Command to run"
    )
    parser.add_argument("--session-id", help="Specific session ID")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    detector = SessionDetector()

    if args.command == "current":
        session_id, method, confidence = detector.get_current_session_id()
        if args.json:
            print(
                json.dumps(
                    {
                        "session_id": session_id,
                        "method": method,
                        "confidence": confidence,
                    }
                )
            )
        else:
            print(f"Session ID: {session_id}")
            print(f"Detection: {method} (confidence: {confidence:.0%})")

    elif args.command == "info":
        info = detector.get_session_info(args.session_id)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            for key, value in info.items():
                print(f"{key}: {value}")

    elif args.command == "path":
        path = detector.get_session_file_path(args.session_id)
        if path:
            print(path)
        else:
            print("Session file not found", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
