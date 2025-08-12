"""
Artifact Ingestion Module
Handles parsing and importing code, documentation, and chat logs.
"""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def scan_artifacts(root_dir):
    artifact_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith((".py", ".md")):
                artifact_files.append(os.path.join(dirpath, fname))
    return artifact_files


def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def ingest_all(root_dir="."):
    files = scan_artifacts(root_dir)
    return [(f, read_file(f)) for f in files]


if __name__ == "__main__":
    artifacts = ingest_all()
    print(f"Ingested {len(artifacts)} artifacts.")
    print("Sample:", artifacts[0] if artifacts else "No artifacts found.")
