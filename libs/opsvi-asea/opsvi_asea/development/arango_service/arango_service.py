import os
from flask import Flask, request, jsonify
from arango import ArangoClient
from arango.exceptions import AQLQueryExecuteError

app = Flask(__name__)

# --- Configuration ---
# It's better to use environment variables for sensitive data
ARANGO_HOST = os.getenv("ARANGO_HOST", "http://127.0.0.1:8531")
ARANGO_DB_NAME = os.getenv("ARANGO_DB_NAME", "asea_prod_db")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "arango_production_password")

# --- ArangoDB Client Initialization ---
try:
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    print("Successfully connected to ArangoDB.")
except Exception as e:
    print(f"FATAL: Failed to connect to ArangoDB: {e}")
    client = None
    db = None


def get_db():
    """Returns the database client. Exits if not available."""
    if not db:
        raise ConnectionError("ArangoDB connection is not available.")
    return db


# --- API Endpoints ---


@app.route("/status", methods=["GET"])
def status():
    """Check the status of the service and database connection."""
    if db:
        try:
            # A lightweight query to check the connection
            db.version()
            return jsonify({"status": "ok", "database_connection": "ok"})
        except Exception as e:
            return (
                jsonify(
                    {"status": "ok", "database_connection": "error", "message": str(e)}
                ),
                503,
            )
    else:
        return jsonify({"status": "error", "database_connection": "unavailable"}), 503


@app.route("/aql/query", methods=["POST"])
def aql_query():
    """Execute a raw AQL query."""
    try:
        db_client = get_db()
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "AQL 'query' not provided."}), 400

        query_string = data["query"]
        bind_vars = data.get("bind_vars", {})

        cursor = db_client.aql.execute(query_string, bind_vars=bind_vars)
        result_list = [doc for doc in cursor]
        return jsonify({"result": result_list})

    except AQLQueryExecuteError as e:
        return (
            jsonify(
                {
                    "error": f"AQL Execution Error: {e.message}",
                    "details": e.response.text,
                }
            ),
            400,
        )
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/documents/get", methods=["POST"])
def get_document():
    """Get a document by its _key."""
    try:
        db_client = get_db()
        data = request.get_json()
        collection_name = data.get("collection")
        key = data.get("key")
        if not all([collection_name, key]):
            return jsonify({"error": "Collection and key must be provided."}), 400

        if not db_client.has_collection(collection_name):
            return jsonify({"error": f"Collection '{collection_name}' not found."}), 404

        collection = db_client.collection(collection_name)
        doc = collection.get(key)

        if doc is None:
            return (
                jsonify(
                    {
                        "error": f"Document with key '{key}' not found in '{collection_name}'."
                    }
                ),
                404,
            )

        return jsonify({"document": doc})

    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/documents/upsert", methods=["POST"])
def upsert_document():
    """Upsert a document into a collection."""
    try:
        db_client = get_db()
        data = request.get_json()
        collection_name = data.get("collection")
        document = data.get("document")

        if not all([collection_name, document]):
            return jsonify({"error": "Collection and document must be provided."}), 400
        if "_key" not in document:
            return jsonify({"error": "Upsert document must contain a '_key'."}), 400

        if not db_client.has_collection(collection_name):
            return jsonify({"error": f"Collection '{collection_name}' not found."}), 404

        query = """
        UPSERT { _key: @key }
        INSERT @doc
        UPDATE @doc
        IN @@collection
        RETURN NEW
        """
        bind_vars = {
            "key": document["_key"],
            "doc": document,
            "@collection": collection_name,
        }
        cursor = db_client.aql.execute(query, bind_vars=bind_vars)
        result = [doc for doc in cursor]
        return jsonify({"upsert_result": result[0] if result else None})

    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/documents/insert", methods=["POST"])
def insert_document():
    """Insert a document into a collection."""
    try:
        db_client = get_db()
        data = request.get_json()
        collection_name = data.get("collection")
        document = data.get("document")
        if not all([collection_name, document]):
            return jsonify({"error": "Collection and document must be provided."}), 400

        if not db_client.has_collection(collection_name):
            return jsonify({"error": f"Collection '{collection_name}' not found."}), 404

        collection = db_client.collection(collection_name)
        result = collection.insert(document)
        return jsonify({"insert_result": result})

    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/collections/create", methods=["POST"])
def create_collection():
    """Create a collection if it doesn't exist."""
    try:
        db_client = get_db()
        data = request.get_json()
        collection_name = data.get("name")
        if not collection_name:
            return jsonify({"error": "Collection 'name' must be provided."}), 400

        if not db_client.has_collection(collection_name):
            db_client.create_collection(collection_name)
            return jsonify({"message": f"Collection '{collection_name}' created."}), 201
        else:
            return (
                jsonify({"message": f"Collection '{collection_name}' already exists."}),
                200,
            )

    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    # Use host='0.0.0.0' to be accessible from other containers/machines
    app.run(host="0.0.0.0", port=5001, debug=True)
