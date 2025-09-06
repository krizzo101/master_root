#!/usr/bin/env python3
"""
File Organization Guidance Hook
Provides project structure reminders before file operations
"""
import json
import os
import sys


def get_file_guidance(file_path):
    """Return guidance based on file path and project structure rules"""
    guidance = []

    if not file_path:
        return guidance

    # Get filename and extension
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    # Skip if not a file type we care about
    if ext not in [".md", ".txt", ".rst", ".json", ".yaml", ".yml"]:
        return guidance

    # Project structure rules
    if file_path.startswith("/home/opsvi/master_root/"):
        relative_path = file_path.replace("/home/opsvi/master_root/", "")

        # Documentation files guidance
        if ext in [".md", ".txt", ".rst"]:
            guidance.append("📁 FILE ORGANIZATION REMINDER:")
            guidance.append("   • Agent knowledge/notes → .claude/knowledge/docs/")
            guidance.append("   • Project deliverables → apps/[app-name]/docs/")
            guidance.append("   • Allowed in root: CLAUDE.md, README.md, my_notes.txt")

            # Check if it's going to root inappropriately
            if "/" not in relative_path and filename not in [
                "CLAUDE.md",
                "README.md",
                "my_notes.txt",
            ]:
                guidance.append("   ⚠️  Consider: Is this for agents or humans?")

        # Configuration files guidance
        elif ext in [".json", ".yaml", ".yml"]:
            guidance.append("⚙️  CONFIG FILE REMINDER:")
            guidance.append("   • App configs → apps/[app-name]/")
            guidance.append("   • Agent configs → .claude/")
            guidance.append("   • Project configs → project root (package.json, etc.)")

    return guidance


def main():
    try:
        # Read tool data from stdin
        tool_data = json.load(sys.stdin)
        tool_input = tool_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        # Get guidance
        guidance = get_file_guidance(file_path)

        # Print guidance (non-blocking)
        if guidance:
            print("")
            for line in guidance:
                print(line)
            print("")

        # Always allow the operation (exit 0)
        sys.exit(0)

    except Exception:
        # Fail gracefully - never block user operations
        sys.exit(0)


if __name__ == "__main__":
    main()
