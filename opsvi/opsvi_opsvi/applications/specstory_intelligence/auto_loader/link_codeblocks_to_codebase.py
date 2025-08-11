#!/usr/bin/env python3
"""
Enhanced linkage: Link SpecStory code_block nodes to codebase modules by tool/script name.
"""

import re

from arango import ArangoClient
from arango.exceptions import ServerConnectionError

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
CODEBLOCK_COLL = "specstory_components"
MODULE_COLL = "modules"
LINK_COLL = "codeblock_links"

SCRIPT_REGEX = r'"([\w_]+\.py)"'
TOOL_REGEX = r'"([\w_]+)"'


def extract_names(text):
    scripts = re.findall(SCRIPT_REGEX, text)
    tools = re.findall(TOOL_REGEX, text)
    # Remove .py from tool names if present in both
    tool_names = set(t for t in tools if not t.endswith(".py"))
    return set(scripts) | tool_names


def main():
    print(f"Connecting to ArangoDB at {ARANGO_URL} ...")
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    # Ensure edge collection exists
    if not db.has_collection(LINK_COLL):
        db.create_collection(LINK_COLL, edge=True)

    codeblocks = [
        d
        for d in db.collection(CODEBLOCK_COLL).all()
        if d.get("component_type") == "code_block"
    ]
    modules = list(db.collection(MODULE_COLL).all())
    module_names = {m["_key"]: m["name"].lower() for m in modules if "name" in m}

    # Build a set of (from, to) to avoid duplicate edges
    existing_edges = set()
    for e in db.collection(LINK_COLL).all():
        existing_edges.add((e["_from"], e["_to"]))

    total_links = 0
    unmatched = 0
    for cb in codeblocks:
        cb_content = cb.get("content", {}).get("raw_content", "")
        names = extract_names(cb_content)
        found = False
        for mod_key, mod_name in module_names.items():
            for name in names:
                if name.lower() in mod_name or mod_name in name.lower():
                    from_id = f"{CODEBLOCK_COLL}/{cb['_key']}"
                    to_id = f"{MODULE_COLL}/{mod_key}"
                    if (from_id, to_id) not in existing_edges:
                        db.collection(LINK_COLL).insert(
                            {
                                "_from": from_id,
                                "_to": to_id,
                                "type": "links_to_code",
                                "matched_name": name,
                            }
                        )
                        existing_edges.add((from_id, to_id))
                        total_links += 1
                        found = True
        if not found:
            unmatched += 1
    print(f"Total code_blocks: {len(codeblocks)}")
    print(f"Total links created: {total_links}")
    print(f"Unmatched code_blocks: {unmatched}")


if __name__ == "__main__":
    main()
