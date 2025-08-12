#!/usr/bin/env python3
"""
Find and report the most influential nodes in the SpecStory graph (degree, PageRank).
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

    print("\nTop 10 nodes by degree (in+out):")
    degree_query = f"""
    FOR v IN {VERTEX_COLLECTION}
      LET deg = LENGTH(FOR e IN {EDGE_COLLECTION} FILTER e._from == v._id OR e._to == v._id RETURN 1)
      SORT deg DESC
      LIMIT 10
      RETURN {{_key: v._key, component_type: v.component_type, degree: deg}}
    """
    try:
        results = list(db.aql.execute(degree_query))
        print(f"{'Key':<40} {'Type':<20} {'Degree':<6}")
        print("-" * 70)
        for r in results:
            print(f"{r['_key']:<40} {r['component_type']:<20} {r['degree']:<6}")
    except Exception as e:
        print(f"❌ Failed to compute degree: {e}")

    # Try Pregel PageRank (if available)
    print("\nPageRank (Pregel, top 10):")
    try:
        # Start Pregel job
        job = db.pregel.create_job(
            algorithm="pagerank",
            graph="specstory_graph",
            params={"resultField": "pagerank", "maxGSS": 20},
        )
        print(f"Pregel job started: {job['id']}, waiting...")
        import time

        while True:
            status = db.pregel.job(job["id"])
            if status["state"] in ("done", "canceled", "fatal error"):
                break
            time.sleep(1)
        if status["state"] != "done":
            print(f"Pregel failed: {status['state']}")
        else:
            # Query top 10 by pagerank
            pr_query = f"""
            FOR v IN {VERTEX_COLLECTION}
              SORT v.pagerank DESC
              LIMIT 10
              RETURN {{_key: v._key, component_type: v.component_type, pagerank: v.pagerank}}
            """
            pr_results = list(db.aql.execute(pr_query))
            print(f"{'Key':<40} {'Type':<20} {'PageRank':<10}")
            print("-" * 70)
            for r in pr_results:
                print(
                    f"{r['_key']:<40} {r['component_type']:<20} {r.get('pagerank', 0):<10.4f}"
                )
    except Exception as e:
        print(f"(Pregel PageRank not available: {e})")


if __name__ == "__main__":
    main()
