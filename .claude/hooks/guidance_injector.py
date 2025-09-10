#!/usr/bin/env python3
"""
Contextual Guidance Injection System
Provides just-in-time reminders to agents based on their actions
"""
import json
import re
import sys


def analyze_tool_input(tool_data):
    """Analyze tool input and return contextual guidance if needed"""
    tool_name = tool_data.get("tool_name", "")
    tool_input = tool_data.get("tool_input", {})

    guidance = []

    # File Organization Guidance
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        if file_path:
            guidance.extend(check_file_placement(file_path))

    # Knowledge Management Guidance
    if tool_name in ["Write", "Edit"]:
        content = tool_input.get("content", "") + tool_input.get("new_string", "")
        guidance.extend(check_knowledge_patterns(content))

    # Testing Evidence Guidance
    if "content" in tool_input or "new_string" in tool_input:
        content = tool_input.get("content", "") + tool_input.get("new_string", "")
        guidance.extend(check_evidence_requirements(content))

    return guidance


def check_file_placement(file_path):
    """Check if file placement follows organizational rules"""
    guidance = []

    # Check for documentation files in project root
    if file_path.endswith((".md", ".txt", ".rst")):
        if "/master_root/" in file_path and ".claude/knowledge" not in file_path:
            # Allow specific exceptions
            allowed_root_files = ["CLAUDE.md", "README.md", "my_notes.txt"]
            filename = file_path.split("/")[-1]
            if filename not in allowed_root_files:
                guidance.append(
                    "🚨 CRITICAL: Documentation files must go in .claude/knowledge/ subdirectories, NOT project root"
                )
                guidance.append("   Example: .claude/knowledge/docs/filename.md")

    return guidance


def check_knowledge_patterns(content):
    """Check for content that should be stored in knowledge base"""
    guidance = []

    discovery_patterns = [
        r"\b(discovered|found|learned|identified)\b",
        r"\b(working|successful|tested|verified)\b",
        r"\b(solution|fix|workaround)\b",
    ]

    for pattern in discovery_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            guidance.append("💡 Consider storing this insight in knowledge base")
            guidance.append(
                "   Use: mcp__knowledge__knowledge_store with evidence and tags"
            )
            break

    return guidance


def check_evidence_requirements(content):
    """Check for claims that need evidence"""
    guidance = []

    claim_patterns = [
        r"\b(works|working|successful|tested|verified|confirmed)\b",
        r"\b(completed|finished|implemented|fixed)\b",
    ]

    for pattern in claim_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            if "session" not in content.lower() and "evidence" not in content.lower():
                guidance.append(
                    "📋 Include evidence for claims: session ID, methodology, specific test results"
                )
            break

    return guidance


def main():
    """Main hook entry point"""
    try:
        # Read tool data from stdin
        if sys.stdin.isatty():
            return  # No data from hook system

        tool_data = json.load(sys.stdin)

        # Analyze and generate guidance
        guidance = analyze_tool_input(tool_data)

        # Output guidance if any
        if guidance:
            print("\n🤖 CONTEXTUAL GUIDANCE:")
            for item in guidance:
                print(f"   {item}")
            print()

    except Exception as e:
        # Fail gracefully - don't block user operations
        pass


if __name__ == "__main__":
    main()
