#!/usr/bin/env python3
"""
Generate a summary of a session in the SpecStory graph.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    print("\nSession summary (first session):")
    aql = f"""
    LET session = FIRST(FOR s IN {VERTEX_COLLECTION} FILTER s.component_type == 'session_header' RETURN s)
    LET turns = (
      FOR v, e IN 1..2 OUTBOUND session._id {EDGE_COLLECTION}
        FILTER v.component_type == 'conversation_turn'
        RETURN v
    )
    LET tools = (
      FOR v, e IN 1..2 OUTBOUND session._id {EDGE_COLLECTION}
        FILTER v.component_type == 'tool_call'
        RETURN v
    )
    LET thinking = (
      FOR v, e IN 1..2 OUTBOUND session._id {EDGE_COLLECTION}
        FILTER v.component_type == 'thinking_block'
        RETURN v
    )
    LET code = (
      FOR v, e IN 1..2 OUTBOUND session._id {EDGE_COLLECTION}
        FILTER v.component_type == 'code_block'
        RETURN v
    )
    RETURN (
      session == null ? {{
        session_title: null,
        session_timestamp: null,
        session_obj: null,
        turns: [],
        tools: [],
        thinking: [],
        code: []
      }} : {{
        session_title: session.metadata != null ? session.metadata.session_title || null : null,
        session_timestamp: session.metadata != null ? session.metadata.session_timestamp || null : null,
        session_obj: session,
        turns: turns,
        tools: tools,
        thinking: thinking,
        code: code
      }}
    )
    """
    try:
        results = list(db.aql.execute(aql))
        if not results or not results[0].get("session_title"):
            print("No session found or session metadata missing. Raw session object:")
            print(results[0].get("session_obj"))
            return
        r = results[0]
        print(
            f"Session: {r.get('session_title', '')} | Timestamp: {r.get('session_timestamp', '')}"
        )
        print(
            f"Turns: {len(r.get('turns', []))} | Tool Calls: {len(r.get('tools', []))} | Thinking Blocks: {len(r.get('thinking', []))} | Code Blocks: {len(r.get('code', []))}"
        )
        print("\nSample Turn:")
        if r.get("turns"):
            t = r["turns"][0]
            try:
                print(
                    f"  Speaker: {t['content']['processed_content'].get('speaker', '')}"
                )
                print(
                    f"  Content: {t['content']['processed_content'].get('content_raw', '')[:120]}"
                )
            except Exception:
                print("  (Could not extract turn details)")
        print("\nSample Tool Call:")
        if r.get("tools"):
            tc = r["tools"][0]
            try:
                print(
                    f"  Tool: {tc['content']['processed_content'].get('tool_name', '')}"
                )
                print(
                    f"  Params: {tc['content']['processed_content'].get('parameters', '')}"
                )
            except Exception:
                print("  (Could not extract tool call details)")
        print("\nSample Thinking Block:")
        if r.get("thinking"):
            th = r["thinking"][0]
            try:
                print(
                    f"  Summary: {th['content']['processed_content'].get('summary', '')}"
                )
                print(
                    f"  Content: {th['content']['processed_content'].get('content', '')[:120]}"
                )
            except Exception:
                print("  (Could not extract thinking block details)")
        print("\nSample Code Block:")
        if r.get("code"):
            cb = r["code"][0]
            try:
                print(
                    f"  Language: {cb['content']['processed_content'].get('language', '')}"
                )
                print(
                    f"  Content: {cb['content']['processed_content'].get('content', '')[:120]}"
                )
            except Exception:
                print("  (Could not extract code block details)")
    except Exception as e:
        print(f"❌ Failed to summarize session: {e}")


if __name__ == "__main__":
    main()
