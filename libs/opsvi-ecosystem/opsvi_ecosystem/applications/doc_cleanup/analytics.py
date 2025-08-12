"""
Analytics Engine
Provides insights, health metrics, and knowledge gap analysis from the knowledge graph.
"""

from graph_manager import get_db


def run_analytics():
    db = get_db()
    col = db.collection("artifacts")
    count = col.count()
    print(f"Total artifacts in graph: {count}")


if __name__ == "__main__":
    run_analytics()
