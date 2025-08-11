#!/usr/bin/env python3
"""
Session/Episode Summarization and Self-Improvement Analytics
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
SESSIONS_COLL = "specstory_sessions"
TOOL_COLL = "tool_interactions"
ANALYTICS_COLL = "session_analytics"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    # Get 5 most recent sessions
    sessions = sorted(
        db.collection(SESSIONS_COLL).all(),
        key=lambda s: s.get("timestamp", ""),
        reverse=True,
    )[:5]

    for sess in sessions:
        print("\n---\nSession Summary:")
        print(f"Session ID: {sess.get('session_id')}")
        print(f"Title: {sess.get('title', sess.get('session_name', ''))}")
        print(f"Timestamp: {sess.get('timestamp')}")
        print(f"User Intent: {sess.get('user_intent', '')}")
        print(f"Outcome: {sess.get('session_outcome', '')}")
        print(f"File Path: {sess.get('file_path', '')}")

        # Tool usage
        tools = [
            t
            for t in db.collection(TOOL_COLL).all()
            if t.get("session_id") == sess.get("session_id")
        ]
        tool_names = set(t.get("tool_name") for t in tools)
        success_count = sum(1 for t in tools if t.get("execution_status") == "success")
        error_count = sum(1 for t in tools if t.get("execution_status") == "error")
        print(f"Tools Used: {', '.join(tool_names) if tool_names else 'None'}")
        print(f"Tool Successes: {success_count}  Errors: {error_count}")

        # Analytics
        analytics = next(
            (
                a
                for a in db.collection(ANALYTICS_COLL).all()
                if a.get("session_id") == sess.get("session_id")
            ),
            None,
        )
        if analytics:
            print(
                f"Turns: {analytics.get('total_turns', '?')}, Tools Used: {analytics.get('total_tools_used', '?')}, Complexity: {analytics.get('session_complexity', '?')}"
            )
            if analytics.get("error_analysis"):
                print(f"Error Analysis: {analytics['error_analysis']}")
            if analytics.get("success_indicators"):
                print(f"Success Indicators: {analytics['success_indicators']}")
        else:
            print("No analytics available.")

        # Improvement suggestions
        if error_count > 0:
            print(
                "Improvement Suggestion: Review error patterns and tool usage for possible workflow or tool selection improvements."
            )
        elif not tools:
            print(
                "Improvement Suggestion: No tools used; consider leveraging available tools for efficiency."
            )
        else:
            print(
                "Improvement Suggestion: Continue current workflow; monitor for new issues."
            )


if __name__ == "__main__":
    main()
