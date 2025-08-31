#!/usr/bin/env python3
import json
import os
import re
import sys


def fail(msg):
    sys.stderr.write(msg)
    sys.exit(2)  # 2 = block the tool call


def main():
    try:
        inp = json.load(sys.stdin)
        tool = inp.get("tool_name", "")
        ti = inp.get("tool_input", {}) or {}
        path = ti.get("file_path") or ti.get("path") or ""
        cmd = (ti.get("command") or ti.get("cmd") or "").strip()
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: safety_gate.py:main() -- tool={tool}, path={path[:50]}",
                file=sys.stderr,
            )

        blocked_files = (
            r"\.env$",
            r"(^|/)\.git/",
            r"(^|/)secrets\.json$",
            r"(^|/)prod/",
        )
        dangerous_cmds = (
            r"\brm\s+-rf\s+/?\b",
            r"\bsudo\s+\b",
            r":\(\)\s*\{\s*:\|\:&\s*;\s*\}\s*;:",
        )

        if (
            tool in ("Edit", "Write")
            and path
            and any(re.search(p, path) for p in blocked_files)
        ):
            # TODO: temporary print-based debug — replace with proper logger before merge/release
            if os.getenv("DEBUG"):
                print(
                    f"DEBUG: safety_gate.py:main() -- blocking edit to {path}",
                    file=sys.stderr,
                )
            fail(f"Blocked edit to protected path: {path}")
        if tool == "Bash" and cmd and any(re.search(p, cmd) for p in dangerous_cmds):
            # TODO: temporary print-based debug — replace with proper logger before merge/release
            if os.getenv("DEBUG"):
                print(
                    f"DEBUG: safety_gate.py:main() -- blocking command: {cmd[:50]}...",
                    file=sys.stderr,
                )
            fail(f"Blocked dangerous command: `{cmd}`")

        sys.exit(0)
    except Exception as e:
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(f"DEBUG: safety_gate.py:main() -- exception={e}", file=sys.stderr)
        # If guard fails, default to safe side: block with generic message
        fail("Blocked by safety gate due to hook error.")


if __name__ == "__main__":
    main()
