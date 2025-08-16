from arango import ArangoClient, DocumentUpdateError
from datetime import datetime, timezone

# --- Configuration ---
# In a real production environment, these should come from environment variables or a secure config file.
ARANGO_HOST = "http://localhost:8529"
ARANGO_USER = "root"
ARANGO_PASSWORD = (
    "arango_dev_password"  # Use the correct password found in project scripts
)
DB_NAME = "asea_prod_db"
COLLECTION_NAME = "entities"

# --- Main Logic ---


def connect_to_arango():
    """Establishes connection to the ArangoDB database using python-arango."""
    try:
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
        print("Successfully connected to ArangoDB.")
        return db
    except Exception as e:
        print(f"Failed to connect to ArangoDB: {e}")
        return None


def calculate_completeness(doc):
    """Calculates a completeness score based on the presence of key fields."""
    # Define the set of fields that constitute a 'complete' document according to Rule 602
    required_fields = [
        "title",
        "content",
        "category",
        "semantic_tags",
        "provenance",
        "quality_grade",
        "validation_status",
        "confidence_level",
        "change_log",
    ]

    present_fields_count = 0
    for field in required_fields:
        if field in doc and doc[field] is not None and doc[field] != "":
            present_fields_count += 1

    return round(present_fields_count / len(required_fields), 2)


def generate_semantic_tags(doc):
    """Generates a basic set of semantic tags from the title and category."""
    tags = set()
    if "category" in doc and doc["category"]:
        tags.add(doc["category"].lower().replace("_", "-"))

    if "title" in doc and doc["title"]:
        # Simple tokenization: split by space and common delimiters, take non-trivial words
        words = doc["title"].lower().replace("-", " ").replace("_", " ").split()
        for word in words:
            # Filter out common stop words and very short words
            if len(word) > 3 and word not in ["the", "for", "and", "with", "into"]:
                tags.add(word)
    return list(tags)


def enhance_data_quality(db):
    """
    Audits and enhances all documents in the specified collection to conform to Rule 602.
    """
    if not db.has_collection(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' not found in database '{DB_NAME}'.")
        return

    entities_collection = db.collection(COLLECTION_NAME)
    cursor = entities_collection.all()
    total_docs = cursor.count()
    print(f"Found {total_docs} documents to process in '{COLLECTION_NAME}'.")

    processed_count = 0
    for doc in cursor:
        updated = False
        update_payload = {}

        # 1. Validate and add change_log
        change_log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "changes": "Automated data quality enhancement script run.",
            "author": "agent/data-quality-enhancer",
        }
        current_change_log = doc.get("change_log", [])
        if not current_change_log:
            update_payload["change_log"] = [change_log_entry]
            updated = True
        else:
            # If a log exists, increment the version number for the new entry
            try:
                latest_version = float(current_change_log[-1].get("version", "0.0"))
                change_log_entry["version"] = str(round(latest_version + 0.1, 1))
            except (ValueError, KeyError):
                change_log_entry["version"] = "2.0"  # Fallback

            current_change_log.append(change_log_entry)
            update_payload["change_log"] = current_change_log
            updated = True

        # 2. Validate and add semantic_tags
        if not doc.get("semantic_tags"):
            update_payload["semantic_tags"] = generate_semantic_tags(doc)
            updated = True

        # 3. Validate and add validation_status
        if "validation_status" not in doc:
            update_payload["validation_status"] = "pending_review"
            updated = True

        # 4. Validate and add quality_grade
        if "quality_grade" not in doc:
            update_payload[
                "quality_grade"
            ] = "C"  # Default grade for unverified, auto-enhanced data
            updated = True

        # 5. Calculate and update completeness_score (always recalculate for consistency)
        # To do this, we need to apply the potential updates to the document object first
        temp_doc_for_calc = doc.copy()
        temp_doc_for_calc.update(update_payload)

        new_completeness_score = calculate_completeness(temp_doc_for_calc)
        if doc.get("completeness_score") != new_completeness_score:
            update_payload["completeness_score"] = new_completeness_score
            updated = True

        # If any updates were made, save the document
        if updated:
            try:
                entities_collection.update(doc, update_payload)
                processed_count += 1
                print(
                    f"  -> Updated doc: {doc['_key']} (Score: {update_payload.get('completeness_score', 'N/A')})"
                )
            except DocumentUpdateError as e:
                print(f"  -> FAILED to update doc: {doc['_key']}. Error: {e}")

    print("\nData quality enhancement complete.")
    print(
        f"Successfully processed and updated {processed_count} out of {total_docs} documents."
    )


if __name__ == "__main__":
    db_connection = connect_to_arango()
    if db_connection:
        enhance_data_quality(db_connection)
