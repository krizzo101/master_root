#!/usr/bin/env python3
import json
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
            fail(f"Blocked edit to protected path: {path}")
        if tool == "Bash" and cmd and any(re.search(p, cmd) for p in dangerous_cmds):
            fail(f"Blocked dangerous command: `{cmd}`")

        sys.exit(0)
    except Exception:
        # If guard fails, default to safe side: block with generic message
        fail("Blocked by safety gate due to hook error.")


if __name__ == "__main__":
    main()
