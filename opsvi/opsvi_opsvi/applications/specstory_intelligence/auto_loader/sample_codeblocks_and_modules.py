#!/usr/bin/env python3
"""
Sample code block content and module names from ArangoDB.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
CODEBLOCK_COLL = "specstory_components"
MODULE_COLL = "modules"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    print("\nSample code_blocks:")
    codeblocks = [
        d
        for d in db.collection(CODEBLOCK_COLL).all()
        if d.get("component_type") == "code_block"
    ]
    for cb in codeblocks[:5]:
        content = cb.get("content", {}).get("raw_content", "")
        print(f"- _key: {cb['_key']}\n  content: {content[:200].replace('\n',' ')}\n")

    print("\nSample modules:")
    modules = list(db.collection(MODULE_COLL).all())
    for m in modules[:5]:
        print(f"- _key: {m['_key']}  name: {m.get('name','')}\n")


if __name__ == "__main__":
    main()
