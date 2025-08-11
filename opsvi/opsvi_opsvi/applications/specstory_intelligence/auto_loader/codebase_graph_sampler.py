#!/usr/bin/env python3
"""
Sample all collections in ArangoDB: list collections, sample docs, print type/kind fields.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"

FIELDS = ["type", "kind", "node_type", "entity_type", "edge_type", "relationship_type"]


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    print("\nAll collections:")
    for coll in db.collections():
        if coll["name"].startswith("_"):
            continue  # skip system collections
        print(f"- {coll['name']}")
        try:
            docs = list(db.collection(coll["name"]).all())[:3]
            for d in docs:
                print(f"  Sample: {d}")
            for field in FIELDS:
                vals = set(d.get(field) for d in docs if field in d)
                if vals:
                    print(f"  Unique '{field}': {vals}")
        except Exception as e:
            print(f"  (Error reading collection: {e})")


if __name__ == "__main__":
    main()
