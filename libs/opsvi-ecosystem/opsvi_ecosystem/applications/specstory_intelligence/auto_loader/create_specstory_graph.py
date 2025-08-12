#!/usr/bin/env python3
"""
Automate creation of the SpecStory graph in ArangoDB using collections populated by the auto loader.
"""

from arango import ArangoClient
from arango.exceptions import (
    CollectionCreateError,
    GraphCreateError,
    ServerConnectionError,
)

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"
GRAPH_NAME = "specstory_graph"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect to ArangoDB: {e}")
        return
    print("✅ Connected.")

    # Ensure vertex collection exists
    if not db.has_collection(VERTEX_COLLECTION):
        try:
            db.create_collection(VERTEX_COLLECTION)
            print(f"✅ Created vertex collection: {VERTEX_COLLECTION}")
        except CollectionCreateError as e:
            print(f"❌ Failed to create vertex collection: {e}")
            return
    else:
        print(f"✔️ Vertex collection exists: {VERTEX_COLLECTION}")

    # Ensure edge collection exists
    if not db.has_collection(EDGE_COLLECTION):
        try:
            db.create_collection(EDGE_COLLECTION, edge=True)
            print(f"✅ Created edge collection: {EDGE_COLLECTION}")
        except CollectionCreateError as e:
            print(f"❌ Failed to create edge collection: {e}")
            return
    else:
        print(f"✔️ Edge collection exists: {EDGE_COLLECTION}")

    # Create the graph
    if not db.has_graph(GRAPH_NAME):
        try:
            db.create_graph(
                GRAPH_NAME,
                edge_definitions=[
                    {
                        "edge_collection": EDGE_COLLECTION,
                        "from_vertex_collections": [VERTEX_COLLECTION],
                        "to_vertex_collections": [VERTEX_COLLECTION],
                    }
                ],
            )
            print(f"✅ Created graph: {GRAPH_NAME}")
        except GraphCreateError as e:
            print(f"❌ Failed to create graph: {e}")
            return
    else:
        print(f"✔️ Graph already exists: {GRAPH_NAME}")

    print("🎉 SpecStory graph setup complete.")


if __name__ == "__main__":
    main()
