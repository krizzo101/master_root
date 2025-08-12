from datetime import datetime
from pathlib import Path
import re

import yaml

# --- Load Pattern Catalog ---
PATTERN_CATALOG_PATH = Path("config/log_cleaning_patterns.yml")
with open(PATTERN_CATALOG_PATH, encoding="utf-8") as f:
    pattern_catalog = yaml.safe_load(f)
patterns = pattern_catalog.get("patterns", [])

# --- Directories ---
RAW_LOGS_DIR = Path(".specstory/history")
CLEANED_LOGS_DIR = Path(".cursor/import")
CLEANED_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --- Utility: Compile regexes ---
compiled_patterns = []
for pat in patterns:
    try:
        compiled_patterns.append(
            {
                "name": pat["name"],
                "description": pat.get("description", ""),
                "regex": re.compile(pat["regex"]),
                "cleaning": pat.get("cleaning", []),
            }
        )
    except Exception as e:
        print(f"Pattern compile error: {pat['name']} - {e}")


# --- Cleaning Functions ---
def standardize_timestamp(line):
    # Example: [2025-07-03 09:19:00] <user> ...
    # Standardize to ISO 8601
    match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] <([^>]+)> (.+)", line)
    if match:
        dt, user, msg = match.groups()
        try:
            dt_iso = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").isoformat()
            return f"[{dt_iso}] <{user}> {msg}"
        except Exception:
            return line
    return line


def trim_whitespace(line):
    return line.strip()


def remove_if_junk(line):
    # Placeholder: could use more advanced heuristics
    return None if "junk" in line.lower() else line


def remove(line):
    return None


def deduplicate(blocks):
    seen = set()
    deduped = []
    for block in blocks:
        h = hash(block)
        if h not in seen:
            deduped.append(block)
            seen.add(h)
    return deduped


CLEANING_ACTIONS = {
    "standardize_timestamp": standardize_timestamp,
    "trim_whitespace": trim_whitespace,
    "remove_if_junk": remove_if_junk,
    "remove": remove,
}


# --- Main Cleaning Logic ---
def classify_line(line):
    for pat in compiled_patterns:
        if pat["regex"].match(line):
            return pat["name"], pat["cleaning"]
    return "unclassified", []


def clean_log_file(input_path, output_dir):
    audit_log = []
    cleaned_lines = []
    with open(input_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            orig_line = line.rstrip("\n")
            pat_name, actions = classify_line(orig_line)
            cleaned = orig_line
            for action in actions:
                func = CLEANING_ACTIONS.get(action["action"])
                if func:
                    result = func(cleaned)
                    if result is None:
                        audit_log.append(
                            {
                                "line": idx + 1,
                                "pattern": pat_name,
                                "action": action["action"],
                                "removed": True,
                                "original": orig_line,
                            }
                        )
                        cleaned = None
                        break
                    elif result != cleaned:
                        audit_log.append(
                            {
                                "line": idx + 1,
                                "pattern": pat_name,
                                "action": action["action"],
                                "transformed": True,
                                "original": cleaned,
                                "new": result,
                            }
                        )
                        cleaned = result
            if cleaned is not None:
                cleaned_lines.append(cleaned)
    # Deduplication phase (block-level, simple for now)
    deduped_lines = deduplicate(cleaned_lines)
    # Write cleaned log
    out_cleaned = output_dir / (input_path.name + ".cleaned.md")
    with open(out_cleaned, "w", encoding="utf-8") as f:
        for line in deduped_lines:
            f.write(line + "\n")
    # Write audit log
    out_audit = output_dir / (input_path.name + ".audit.yml")
    with open(out_audit, "w", encoding="utf-8") as f:
        yaml.dump(audit_log, f, allow_unicode=True)
    return out_cleaned, out_audit


# --- Batch Processing ---
def main():
    for log_file in RAW_LOGS_DIR.glob("*.md"):
        print(f"Processing {log_file} ...")
        cleaned, audit = clean_log_file(log_file, CLEANED_LOGS_DIR)
        print(f"  Cleaned: {cleaned}")
        print(f"  Audit:   {audit}")


if __name__ == "__main__":
    main()
