#!/usr/bin/env python3
"""
Extract and summarize the 2-hop neighborhood of a highly connected node in the SpecStory graph.
"""

from collections import Counter

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"
NODE_KEY = "1919f2b2-1906-4a20-89ea-a3cb6bc024e0"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    print(f"\nExtracting 2-hop neighborhood of node: {NODE_KEY}")
    aql = f"""
    FOR v, e, p IN 1..2 ANY '{VERTEX_COLLECTION}/{NODE_KEY}' GRAPH 'specstory_graph'
      RETURN {{ node: v, edge: e }}
    """
    try:
        results = list(db.aql.execute(aql))
        nodes = [r["node"] for r in results if r["node"]]
        edges = [r["edge"] for r in results if r["edge"]]
        node_types = Counter(
            n["component_type"] for n in nodes if "component_type" in n
        )
        edge_types = Counter(
            e["relationship_type"] for e in edges if e and "relationship_type" in e
        )
        print(f"Node type counts: {dict(node_types)}")
        print(f"Edge type counts: {dict(edge_types)}")
        # Print a sample of each node type
        for t, count in node_types.items():
            sample = next((n for n in nodes if n.get("component_type") == t), None)
            if sample:
                print(f"\nSample {t} node: {sample['_key']}")
                print(
                    f"  Content: {sample.get('content', {}).get('raw_content', '')[:120]}"
                )
        # Print a sample of each edge type
        for t, count in edge_types.items():
            sample = next((e for e in edges if e.get("relationship_type") == t), None)
            if sample:
                print(f"\nSample {t} edge: {sample['_key']}")
                print(f"  From: {sample['_from']} To: {sample['_to']}")
    except Exception as e:
        print(f"❌ Failed to extract subgraph: {e}")


if __name__ == "__main__":
    main()
