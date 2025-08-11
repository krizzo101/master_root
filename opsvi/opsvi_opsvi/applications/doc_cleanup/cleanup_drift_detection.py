from typing import Dict, List

from src.applications.doc_cleanup.agent_utils import (
    extract_code_summary,
    extract_doc_section,
    get_changed_files,
)
from src.shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


def monitor_changes(base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[str]:
    """
    Detect changed files between two git refs.
    """
    changed = get_changed_files(base_ref, target_ref)
    print(f"[monitor_changes] Changed files: {changed}")
    return changed


def detect_drift(
    changed_files: List[str], docs_dir: str = "docs/applications/doc_cleanup/"
) -> List[Dict]:
    """
    For each changed file, compare code and docs using OpenAI. Return list of drift flags.
    """
    drift_flags = []
    client = OpenAIResponsesInterface()
    for file in changed_files:
        if not file.endswith(".py"):
            continue
        code_summary = extract_code_summary(file)
        doc_section = extract_doc_section(file, docs_dir) or ""
        prompt = f"""Compare the following code and documentation. List any mismatches, missing, or outdated documentation.\n\nCode:\n{code_summary}\n\nDocs:\n{doc_section}"""
        try:
            response = client.create_response(
                thread_id="drift-detection-thread",  # Replace with real thread logic if needed
                model="gpt-4.1",
                instructions="You are a documentation drift detector. Identify all mismatches and missing documentation.",
                input=prompt,
            )
            drift = response.get("output_text", "").strip()
            if drift and "no drift" not in drift.lower():
                drift_flags.append({"file": file, "drift": drift})
                print(f"[detect_drift] Drift detected in {file}: {drift}")
            else:
                print(f"[detect_drift] No drift in {file}.")
        except Exception as e:
            print(f"[detect_drift] Error for {file}: {e}")
    return drift_flags


def trigger_cleanup(
    drift_flags: List[Dict], docs_dir: str = "docs/applications/doc_cleanup/"
) -> List[Dict]:
    """
    For each drift, generate a cleanup task (draft doc update using OpenAI). Return list of cleanup tasks.
    """
    cleanup_tasks = []
    client = OpenAIResponsesInterface()
    for drift in drift_flags:
        file = drift["file"]
        code_summary = extract_code_summary(file)
        prompt = f"""Given the following code summary, generate the missing or corrected documentation as described.\n\nCode:\n{code_summary}\n\nDrift:\n{drift['drift']}\n\nWrite the updated documentation section only."""
        try:
            response = client.create_response(
                thread_id="cleanup-thread",  # Replace with real thread logic if needed
                model="gpt-4.1",
                instructions="You are a documentation cleanup agent. Generate the required documentation update.",
                input=prompt,
            )
            doc_update = response.get("output_text", "").strip()
            cleanup_tasks.append({"file": file, "doc_update": doc_update})
            print(f"[trigger_cleanup] Cleanup for {file}: {doc_update[:100]}...")
        except Exception as e:
            print(f"[trigger_cleanup] Error for {file}: {e}")
    return cleanup_tasks
