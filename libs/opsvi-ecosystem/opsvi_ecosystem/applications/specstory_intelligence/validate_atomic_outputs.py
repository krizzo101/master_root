import json
import os
import sys

CATALOG_TYPES = [
    "session_header",
    "conversation_turn",
    "tool_call",
    "tool_result",
    "code_block",
    "file_reference",
    "error_message",
    "explicit_reasoning_block",
    "provenance_comment",
    "file_metadata",
    "details_block",
    "summary_block",
    "think_block",
    "directory_listing",
    "markdown_table",
    "intent_tag",
    "focus_tag",
    "action_tag",
    "reflection_tag",
]

REQUIRED_FIELDS = ["type", "start_line", "end_line", "content"]


def validate_atomic_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            return {"file": filepath, "error": f"JSON decode error: {e}"}
    found_types = set()
    anomalies = []
    for comp in data.get("components", []):
        t = comp.get("type")
        if t:
            found_types.add(t)
        for field in REQUIRED_FIELDS:
            if field not in comp:
                anomalies.append({"component": comp, "missing_field": field})
    missing_types = set(CATALOG_TYPES) - found_types
    return {
        "file": filepath,
        "missing_types": list(missing_types),
        "anomalies": anomalies,
        "total_components": len(data.get("components", [])),
    }


def main(directory):
    results = []
    for fname in os.listdir(directory):
        if fname.endswith(".json"):
            fpath = os.path.join(directory, fname)
            results.append(validate_atomic_file(fpath))
    for r in results:
        print(json.dumps(r, indent=2))
    # Optionally write to a report file
    with open(
        os.path.join(directory, "validation_report.txt"), "w", encoding="utf-8"
    ) as f:
        for r in results:
            f.write(json.dumps(r, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_atomic_outputs.py <directory>")
        sys.exit(1)
    main(sys.argv[1])
