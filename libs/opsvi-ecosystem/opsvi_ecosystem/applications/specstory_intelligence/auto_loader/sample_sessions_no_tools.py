#!/usr/bin/env python3
"""
Sample recent sessions with no tool usage and print their metadata and first conversation turns.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
SESSIONS_COLL = "specstory_sessions"
TURNS_COLL = "conversation_turns"
TOOL_COLL = "tool_interactions"


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
    tool_sessions = set(t.get("session_id") for t in db.collection(TOOL_COLL).all())
    no_tool_sessions = [s for s in sessions if s.get("session_id") not in tool_sessions]
    # Sort by timestamp descending
    no_tool_sessions = sorted(
        no_tool_sessions, key=lambda s: s.get("timestamp", ""), reverse=True
    )[:5]

    for sess in no_tool_sessions:
        print("\n---\nSession with No Tool Usage:")
        print(f"Session ID: {sess.get('session_id')}")
        print(f"Title: {sess.get('title', sess.get('session_name', ''))}")
        print(f"Timestamp: {sess.get('timestamp')}")
        print(f"User Intent: {sess.get('user_intent', '')}")
        print(f"File Path: {sess.get('file_path', '')}")
        # Print first 3 conversation turns
        turns = [
            t
            for t in db.collection(TURNS_COLL).all()
            if t.get("session_id") == sess.get("session_id")
        ]
        turns = sorted(turns, key=lambda t: t.get("turn_number", 0))[:3]
        for t in turns:
            summary = t.get("content_summary") or t.get("content", "")
            print(f"Turn {t.get('turn_number')}: {summary[:160]}")


if __name__ == "__main__":
    main()
