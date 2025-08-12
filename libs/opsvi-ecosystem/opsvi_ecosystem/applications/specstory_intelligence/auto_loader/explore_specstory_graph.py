#!/usr/bin/env python3
"""
Explore the SpecStory graph in ArangoDB and report key metrics and points of interest.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
GRAPH_NAME = "specstory_graph"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect to ArangoDB: {e}")
        return
    print("✅ Connected.")

    # Metrics
    print("\n--- SpecStory Graph Metrics ---")
    try:
        num_nodes = db.collection(VERTEX_COLLECTION).count()
        num_edges = db.collection(EDGE_COLLECTION).count()
        print(f"Total nodes: {num_nodes}")
        print(f"Total edges: {num_edges}")
    except Exception as e:
        print(f"❌ Failed to count nodes/edges: {e}")
        return

    # Top 10 nodes by degree
    print("\nTop 10 nodes by degree (most connected):")
    try:
        # Out-degree
        out_deg = db.aql.execute(
            f"""
            FOR v IN {VERTEX_COLLECTION}
                LET deg = LENGTH(FOR e IN {EDGE_COLLECTION} FILTER e._from == v._id OR e._to == v._id RETURN 1)
                SORT deg DESC
                LIMIT 10
                RETURN {{_key: v._key, degree: deg}}
        """
        )
        for i, node in enumerate(out_deg, 1):
            print(f"{i}. {node['_key']} (degree: {node['degree']})")
    except Exception as e:
        print(f"❌ Failed to compute node degrees: {e}")

    # Relationship type distribution
    print("\nRelationship type distribution:")
    try:
        rel_types = db.aql.execute(
            f"""
            FOR e IN {EDGE_COLLECTION}
                COLLECT type = e.relationship_type WITH COUNT INTO count
                RETURN {{type, count}}
        """
        )
        for rel in rel_types:
            print(f"{rel['type']}: {rel['count']}")
    except Exception as e:
        print(f"❌ Failed to compute relationship type distribution: {e}")

    # Isolated nodes
    print("\nIsolated nodes (degree 0):")
    try:
        isolated = db.aql.execute(
            f"""
            FOR v IN {VERTEX_COLLECTION}
                FILTER LENGTH(FOR e IN {EDGE_COLLECTION} FILTER e._from == v._id OR e._to == v._id RETURN 1) == 0
                LIMIT 10
                RETURN v._key
        """
        )
        isolated_list = list(isolated)
        if isolated_list:
            for node in isolated_list:
                print(f"- {node}")
            if len(isolated_list) == 10:
                print("... (more not shown)")
        else:
            print("None")
    except Exception as e:
        print(f"❌ Failed to find isolated nodes: {e}")

    # Simple cycle/self-loop detection
    print("\nNodes with self-loops:")
    try:
        self_loops = db.aql.execute(
            f"""
            FOR e IN {EDGE_COLLECTION}
                FILTER e._from == e._to
                RETURN e._from
        """
        )
        self_loops_list = list(self_loops)
        if self_loops_list:
            for node in self_loops_list:
                print(f"- {node}")
        else:
            print("None")
    except Exception as e:
        print(f"❌ Failed to detect self-loops: {e}")

    print("\n--- End of Report ---")


if __name__ == "__main__":
    main()
