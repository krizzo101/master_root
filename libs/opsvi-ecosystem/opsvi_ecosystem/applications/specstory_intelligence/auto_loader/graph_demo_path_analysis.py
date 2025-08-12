#!/usr/bin/env python3
"""
Trace a reasoning/action path in the SpecStory graph: thinking_block -> tool_call -> tool_result.
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

    print("\nTracing path: thinking_block -> tool_call -> tool_result (up to 4 steps)")
    aql = f"""
    FOR v1 IN {VERTEX_COLLECTION}
      FILTER v1.component_type == 'thinking_block'
      FOR v2, e1 IN 1..2 OUTBOUND v1._id {EDGE_COLLECTION}
        FILTER v2.component_type == 'tool_call'
        FOR v3, e2 IN 1..2 OUTBOUND v2._id {EDGE_COLLECTION}
          FILTER v3.component_type == 'tool_result'
          LIMIT 1
          RETURN [
            {{ "node": v1, "rel": null }},
            {{ "node": v2, "rel": e1 }},
            {{ "node": v3, "rel": e2 }}
          ]
    """
    try:
        results = list(db.aql.execute(aql))
        if not results:
            print("No such path found.")
            return
        path = results[0]
        print(f"{'Step':<5} {'Node Key':<40} {'Type':<18} {'Rel Type':<14}")
        print("-" * 80)
        for i, step in enumerate(path):
            node = step["node"]
            rel = step["rel"]
            rel_type = rel["relationship_type"] if rel else ""
            print(
                f"{i+1:<5} {node['_key']:<40} {node['component_type']:<18} {rel_type:<14}"
            )
    except Exception as e:
        print(f"❌ Failed to trace path: {e}")


if __name__ == "__main__":
    main()
