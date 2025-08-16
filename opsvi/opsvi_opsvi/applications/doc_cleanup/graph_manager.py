"""
Knowledge Graph Manager
Handles storage and queries in ArangoDB for all artifacts and relationships.
"""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from arango import ArangoClient


def get_db():
    host = os.getenv("ARANGO_HOST", "http://localhost:8529")
    db_name = os.getenv("ARANGO_DB", "doc_cleanup_docs")
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASS", "password")
    client = ArangoClient(hosts=host)
    db = client.db(db_name, username=username, password=password)
    return db


def initialize_schema():
    db = get_db()
    # Example: create collections if not exist
    for col in ["artifacts", "relationships"]:
        if not db.has_collection(col):
            db.create_collection(col)
    # TODO: Add indexes, edge definitions, etc.
    print("ArangoDB schema initialized.")


def update_graph():
    # TODO: Implement graph update logic
    pass


def add_artifact(path, content):
    db = get_db()
    col = db.collection("artifacts")
    col.insert({"path": path, "content": content})


def add_embedding(path, embedding):
    db = get_db()
    col = db.collection("artifacts")
    doc = col.get({"path": path})
    if doc:
        doc["embedding"] = embedding
        col.update(doc)
    else:
        col.insert({"path": path, "embedding": embedding})


if __name__ == "__main__":
    initialize_schema()
    add_artifact("test.py", 'print("hello")')
    add_embedding("test.py", [0.1, 0.2, 0.3])
    print("Test artifact and embedding added.")
