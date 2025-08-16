#!/usr/bin/env python3
"""
Review codeblock_links: print details of linked code blocks and modules.
"""

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
CODEBLOCK_COLL = "specstory_components"
MODULE_COLL = "modules"
LINK_COLL = "codeblock_links"


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    links = list(db.collection(LINK_COLL).all())
    print(f"\nTotal codeblock_links: {len(links)}\n")
    for link in links[:8]:
        from_key = link["_from"].split("/")[-1]
        to_key = link["_to"].split("/")[-1]
        matched_name = link.get("matched_name", "")
        cb = db.collection(CODEBLOCK_COLL).get(from_key)
        mod = db.collection(MODULE_COLL).get(to_key)
        cb_content = (
            cb.get("content", {}).get("raw_content", "")[:120] if cb else "(not found)"
        )
        mod_name = mod.get("name", "(not found)") if mod else "(not found)"
        print(
            f"CodeBlock: {from_key}\n  Content: {cb_content}\nModule: {to_key}\n  Name: {mod_name}\nMatched: {matched_name}\n---"
        )


if __name__ == "__main__":
    main()
