"""
Knowledge Graph Manager
Handles storage and queries in ArangoDB for all artifacts and relationships.
Now uses DirectArangoDB for robust, validated DB access.
"""

import hashlib
import logging
import os
import sys
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.shared.interfaces.database.arango_interface import DirectArangoDB

logger = logging.getLogger("agentic_doc_manager.graph_manager")

# Load config from env
host = os.getenv("ARANGO_HOST", "http://127.0.0.1:8550")
db_name = os.getenv("ARANGO_DB", "agentic_docs")
username = os.getenv("ARANGO_USER", "root")
password = os.getenv("ARANGO_PASS", "password")


def get_db():
    try:
        db = DirectArangoDB(
            host=host, database=db_name, username=username, password=password
        )
        return db
    except Exception as e:
        logger.error(f"Failed to connect to ArangoDB: {e}")
        raise


def initialize_schema():
    try:
        db = get_db()
        for col in ["artifacts", "relationships", "embedding_queue"]:
            if not db.collection_exists(col):
                db.create_collection(col, edge=(col == "relationships"))
                logger.info(f"Created collection: {col}")
        logger.info("ArangoDB schema initialized.")
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        raise


def sanitize_key(path, chunk=None):
    key = path.replace("/", "_").replace("#", "_").replace(".", "_")
    if chunk is not None:
        key = f"{key}_chunk{chunk}"
    if len(key) > 200:
        key = hashlib.sha1(key.encode()).hexdigest()
    return key


def add_artifact(path, content, chunk=None):
    try:
        db = get_db()
        col = "artifacts"
        key = sanitize_key(path, chunk)
        doc = {"_key": key, "path": path, "content": content}
        result = db.batch_insert(col, [doc])
        if not result.get("success"):
            logger.error(f"Failed to add artifact {path}: {result.get('error')}")
        else:
            logger.info(f"Added artifact: {key}")
    except Exception as e:
        logger.error(f"Failed to add artifact {path}: {e}")
        raise


def add_embedding(path, embedding, chunk=None):
    try:
        db = get_db()
        col = "artifacts"
        key = sanitize_key(path, chunk)
        doc_result = db.get_document(col, key)
        if doc_result.get("success") and doc_result.get("document"):
            doc = doc_result["document"]
            doc["embedding"] = embedding
            db.update_document(col, doc)
        else:
            doc = {"_key": key, "path": path, "embedding": embedding}
            db.batch_insert(col, [doc])
        logger.info(f"Added embedding: {key}")
    except Exception as e:
        logger.error(f"Failed to add embedding {path}: {e}")
        raise


def enqueue_embedding_job(path, content, chunk=None):
    try:
        db = get_db()
        col = "embedding_queue"
        if not db.collection_exists(col):
            db.create_collection(col)
        job = {
            "path": path,
            "content": content,
            "chunk": chunk,
            "timestamp": int(time.time()),
        }
        key = sanitize_key(path, chunk)
        job["_key"] = key
        result = db.batch_insert(col, [job])
        if not result.get("success"):
            logger.error(
                f"Failed to enqueue embedding job for {path}: {result.get('error')}"
            )
        else:
            logger.info(f"Enqueued embedding job: {key}")
    except Exception as e:
        logger.error(f"Failed to enqueue embedding job for {path}: {e}")
        raise


def dequeue_embedding_jobs(limit=100):
    try:
        db = get_db()
        col = "embedding_queue"
        if not db.collection_exists(col):
            return []
        result = db.find_documents(col, {}, limit=limit)
        if result.get("success"):
            return result.get("documents", [])
        else:
            logger.error(f"Failed to fetch embedding jobs: {result.get('error')}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch embedding jobs: {e}")
        return []


if __name__ == "__main__":
    initialize_schema()
    add_artifact("test.py", 'print("hello")')
    add_embedding("test.py", [0.1, 0.2, 0.3])
    logger.info("Test artifact and embedding added.")
