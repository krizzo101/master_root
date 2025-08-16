#!/usr/bin/env python3
"""
Find all error messages in the SpecStory graph and show their context.
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

    print("\nAll error messages and their context:")
    aql = f"""
    FOR err IN {VERTEX_COLLECTION}
      FILTER err.component_type == 'error_message'
      LET session = err.metadata.session_title
      LET msg = err.content.raw_content
      LET neighbors = (
        FOR v, e IN 1..1 ANY err._id {EDGE_COLLECTION}
          RETURN {{ key: v._key, type: v.component_type }}
      )
      RETURN {{ key: err._key, session, msg, neighbors }}
    """
    try:
        results = list(db.aql.execute(aql))
        if not results:
            print("No error messages found.")
            return
        for r in results:
            print(f"- Error Node: {r['key']} | Session: {r['session']}")
            print(f"  Message: {r['msg'][:120]}{'...' if len(r['msg']) > 120 else ''}")
            print("  Neighbors:")
            for n in r["neighbors"]:
                print(f"    - {n['type']}: {n['key']}")
            print()
    except Exception as e:
        print(f"❌ Failed to find errors: {e}")


if __name__ == "__main__":
    main()
