import json
import os
import sys
from datetime import datetime

SAMPLE_ANNOTATION = {
    "annotation_id": "AUTO-ANNOTATE-001",
    "scope_level": "component",
    "reviewer": {"type": "agent", "id": "auto_annotator"},
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "review_status": "pending",
    "categories": ["auto"],
    "summary": "Auto-generated annotation for review.",
    "details": "This component was batch-annotated for review.",
    "suggested_action": None,
    "evidence_refs": [],
    "child_annotations": [],
}


def annotate_atomic_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    for comp in data.get("components", []):
        if "annotations" not in comp:
            comp["annotations"] = []
        comp["annotations"].append(SAMPLE_ANNOTATION.copy())
    outpath = filepath.replace(".json", "_annotated.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {
        "file": filepath,
        "annotated_file": outpath,
        "components": len(data.get("components", [])),
    }


def main(directory):
    results = []
    for fname in os.listdir(directory):
        if fname.endswith(".json") and not fname.endswith("_annotated.json"):
            fpath = os.path.join(directory, fname)
            results.append(annotate_atomic_file(fpath))
    for r in results:
        print(json.dumps(r, indent=2))
    # Optionally write to a report file
    with open(
        os.path.join(directory, "annotation_report.txt"), "w", encoding="utf-8"
    ) as f:
        for r in results:
            f.write(json.dumps(r, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_annotate_atomic_outputs.py <directory>")
        sys.exit(1)
    main(sys.argv[1])
