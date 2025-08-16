import os

from src.shared.interfaces.database.arango_interface import DirectArangoDB

db = DirectArangoDB(
    host=os.getenv("ARANGO_URL", "http://127.0.0.1:8550"),
    database=os.getenv("ARANGO_DB", "_system"),
    username=os.getenv("ARANGO_USERNAME", "root"),
    password=os.getenv("ARANGO_PASSWORD", "change_me"),
)


def arango_insert(collection, doc):
    try:
        return db.db.collection(collection).insert(doc)
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_connection():
    try:
        # Simple health check: list collections
        return {"success": True, "collections": db.list_collections()}
    except Exception as e:
        return {"success": False, "error": str(e)}
