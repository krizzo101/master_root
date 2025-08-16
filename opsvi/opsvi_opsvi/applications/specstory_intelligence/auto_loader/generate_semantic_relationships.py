#!/usr/bin/env python3
"""
Generate REFERENCES relationships between code_block nodes in the SpecStory graph based on explicit mentions in code or markdown.
"""

import re

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"

# Simple pattern: look for `# references: <block_id>` in code blocks
REFERENCE_PATTERN = re.compile(r"# references: ([\w\-]+)")


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    codeblocks = [
        d
        for d in db.collection(VERTEX_COLLECTION).all()
        if d.get("component_type") == "code_block"
    ]
    block_by_id = {cb["_key"]: cb for cb in codeblocks}
    total_refs = 0
    for cb in codeblocks:
        raw = cb.get("content", {}).get("raw_content", "")
        for match in REFERENCE_PATTERN.finditer(raw):
            ref_id = match.group(1)
            if ref_id in block_by_id:
                from_id = f"{VERTEX_COLLECTION}/{cb['_key']}"
                to_id = f"{VERTEX_COLLECTION}/{ref_id}"
                # Avoid duplicate edges
                existing = db.aql.execute(
                    f"""
                    FOR e IN {EDGE_COLLECTION}
                        FILTER e._from == @from_id AND e._to == @to_id AND e.relationship_type == 'references'
                        RETURN e
                """,
                    {"from_id": from_id, "to_id": to_id},
                )
                if not list(existing):
                    db.collection(EDGE_COLLECTION).insert(
                        {
                            "_from": from_id,
                            "_to": to_id,
                            "relationship_type": "references",
                            "context": {"source": "generate_semantic_relationships.py"},
                        }
                    )
                    total_refs += 1
    print(f"Total REFERENCES relationships created: {total_refs}")


if __name__ == "__main__":
    main()
