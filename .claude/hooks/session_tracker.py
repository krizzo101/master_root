#!/usr/bin/env python3
"""
Session Tracking Hook
Captures session ID and makes it available for other tools
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add session_manager to path
sys.path.insert(0, "/home/opsvi/master_root/.claude/session_manager")


def main():
    try:
        # Read input from stdin
        inp = json.load(sys.stdin)

        # Extract session ID
        session_id = inp.get("session_id") or inp.get("sessionId") or inp.get("id")

        if session_id:
            # Save to state file
            state_file = (
                Path.home() / ".claude" / "session_manager" / "active_session.json"
            )
            state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {
                "session_id": session_id,
                "project": os.getenv("CLAUDE_PROJECT_ROOT", os.getcwd()),
                "timestamp": datetime.now().isoformat(),
                "pid": os.getpid(),
                "hook_event": inp.get("hook_event_name", "unknown"),
            }

            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

            # Also try to export as environment variable (though this won't persist)
            os.environ["CLAUDE_SESSION_UUID"] = session_id

            # Log for debugging
            if os.getenv("DEBUG"):
                log_file = Path.home() / ".claude" / "session_manager" / "debug.log"
                with open(log_file, "a") as f:
                    f.write(
                        f"{datetime.now().isoformat()} - Captured session: {session_id}\n"
                    )

        # Always pass through - don't interfere with normal operation
        print(json.dumps({"suppressOutput": False}))

    except Exception as e:
        # On error, don't block - just pass through
        if os.getenv("DEBUG"):
            print(f"Session tracker error: {e}", file=sys.stderr)
        print(json.dumps({"suppressOutput": False}))


if __name__ == "__main__":
    main()
