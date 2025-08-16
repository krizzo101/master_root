#!/usr/bin/env python3
"""
Aggregate improvement suggestions, error patterns, and tool issues across all sessions.
"""

from collections import Counter

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
SESSIONS_COLL = "specstory_sessions"
TOOL_COLL = "tool_interactions"
ANALYTICS_COLL = "session_analytics"


def get_improvement_suggestion(tools, error_count):
    if error_count > 0:
        return "Review error patterns and tool usage for possible workflow or tool selection improvements."
    elif not tools:
        return "No tools used; consider leveraging available tools for efficiency."
    else:
        return "Continue current workflow; monitor for new issues."


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    sessions = list(db.collection(SESSIONS_COLL).all())
    improvement_counter = Counter()
    error_type_counter = Counter()
    tool_error_counter = Counter()
    session_count = 0

    for sess in sessions:
        session_count += 1
        sid = sess.get("session_id")
        tools = [
            t for t in db.collection(TOOL_COLL).all() if t.get("session_id") == sid
        ]
        error_count = sum(1 for t in tools if t.get("execution_status") == "error")
        for t in tools:
            if t.get("execution_status") == "error":
                tool_error_counter[t.get("tool_name")] += 1
                if t.get("error_type"):
                    error_type_counter[t.get("error_type")] += 1
        suggestion = get_improvement_suggestion(tools, error_count)
        improvement_counter[suggestion] += 1

    print("\n---\nImprovement Suggestions (by frequency):")
    for suggestion, count in improvement_counter.most_common():
        print(f"- {suggestion} ({count} sessions)")

    print("\n---\nMost Frequent Error Types:")
    for err, count in error_type_counter.most_common():
        print(f"- {err} ({count} occurrences)")
    if not error_type_counter:
        print("- None detected.")

    print("\n---\nMost Problematic Tools (by error count):")
    for tool, count in tool_error_counter.most_common():
        print(f"- {tool} ({count} errors)")
    if not tool_error_counter:
        print("- None detected.")

    print("\n---\nActionable Recommendations:")
    if (
        improvement_counter[
            "No tools used; consider leveraging available tools for efficiency."
        ]
        > 0
    ):
        print(
            "- Encourage more consistent tool usage in sessions to maximize agent capabilities."
        )
    if (
        improvement_counter[
            "Review error patterns and tool usage for possible workflow or tool selection improvements."
        ]
        > 0
    ):
        print("- Investigate and address recurring tool errors and workflow issues.")
    if error_type_counter:
        print("- Focus on resolving the most frequent error types (see above).")
    if tool_error_counter:
        print(
            "- Review and improve the reliability of the most problematic tools (see above)."
        )
    if improvement_counter["Continue current workflow; monitor for new issues."] > 0:
        print(
            "- Maintain and monitor successful workflows, but stay alert for new issues."
        )

    print(f"\nTotal sessions analyzed: {session_count}")


if __name__ == "__main__":
    main()
