#!/usr/bin/env python3
"""
Hybrid search demo: find code blocks and modules by keyword, show their links.
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
    keyword = (
        input("Enter keyword for hybrid search (default: 'agent'): ").strip() or "agent"
    )
    print(f"Searching for keyword: {keyword}\n")

    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    except ServerConnectionError as e:
        print(f"❌ Failed to connect: {e}")
        return
    print("✅ Connected.")

    # Find code blocks
    codeblocks = [
        d
        for d in db.collection(CODEBLOCK_COLL).all()
        if d.get("component_type") == "code_block"
        and keyword.lower() in d.get("content", {}).get("raw_content", "").lower()
    ]
    print(f"Found {len(codeblocks)} code blocks matching '{keyword}':")
    for cb in codeblocks:
        cb_key = cb["_key"]
        cb_content = cb.get("content", {}).get("raw_content", "")[:120]
        # Find linked modules
        links = [
            l for l in db.collection(LINK_COLL).all() if l["_from"].endswith(cb_key)
        ]
        linked_mods = [l["_to"].split("/")[-1] for l in links]
        print(f"- CodeBlock: {cb_key}\n  Content: {cb_content}")
        if linked_mods:
            for mod_key in linked_mods:
                mod = db.collection(MODULE_COLL).get(mod_key)
                print(
                    f"    Linked Module: {mod_key}  Name: {mod.get('name','(not found)')}"
                )
        else:
            print("    No linked modules.")

    # Find modules
    modules = [
        m
        for m in db.collection(MODULE_COLL).all()
        if keyword.lower() in m.get("name", "").lower()
    ]
    print(f"\nFound {len(modules)} modules matching '{keyword}':")
    for mod in modules:
        mod_key = mod["_key"]
        mod_name = mod.get("name", "")
        # Find linked code blocks
        links = [
            l for l in db.collection(LINK_COLL).all() if l["_to"].endswith(mod_key)
        ]
        linked_cbs = [l["_from"].split("/")[-1] for l in links]
        print(f"- Module: {mod_key}  Name: {mod_name}")
        if linked_cbs:
            for cb_key in linked_cbs:
                cb = db.collection(CODEBLOCK_COLL).get(cb_key)
                cb_content = (
                    cb.get("content", {}).get("raw_content", "")[:80]
                    if cb
                    else "(not found)"
                )
                print(f"    Linked CodeBlock: {cb_key}  Content: {cb_content}")
        else:
            print("    No linked code blocks.")


if __name__ == "__main__":
    main()
