"""
Analytics Engine
Provides insights, health metrics, and knowledge gap analysis from the knowledge graph.
"""

from src.applications.agentic_doc_manager.graph_manager import get_db


def run_analytics():
    db = get_db()
    result = db.find_documents("artifacts", {})
    count = len(result["documents"]) if result.get("success") else 0
    print(f"Total artifacts in graph: {count}")


if __name__ == "__main__":
    run_analytics()
