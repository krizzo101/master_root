#!/usr/bin/env python3
"""
Delete the 'specstory_relationships' collection in ArangoDB if it exists.
This is required to recreate it as an edge collection for graph use.
"""

from arango import ArangoClient
from arango.exceptions import CollectionDeleteError, ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
COLLECTION = "specstory_relationships"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect to ArangoDB: {e}")
        return
    print("✅ Connected.")

    if db.has_collection(COLLECTION):
        try:
            db.delete_collection(COLLECTION)
            print(f"✅ Deleted collection: {COLLECTION}")
        except CollectionDeleteError as e:
            print(f"❌ Failed to delete collection: {e}")
            return
    else:
        print(f"✔️ Collection does not exist: {COLLECTION}")

    print("🎉 Collection deletion (if needed) complete.")


if __name__ == "__main__":
    main()
