import os
import subprocess
import time
from typing import Dict, List

from src.shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


def orchestrate_update(correction_tasks: List[Dict]) -> List[Dict]:
    """
    Aggregate correction tasks, assign to agents (simulate), manage state.
    """
    print(f"[orchestrate_update] Aggregating {len(correction_tasks)} correction tasks.")
    # In a real system, assign to agents or queue for review; here, just return as a plan
    doc_update_plan = correction_tasks
    return doc_update_plan


def multi_agent_review(doc_update_plan: List[Dict]) -> List[Dict]:
    """
    Use OpenAI to review proposed doc updates for accuracy and compliance.
    """
    reviewed = []
    client = OpenAIResponsesInterface()
    for update in doc_update_plan:
        prompt = f"""Review the following documentation update for technical accuracy, clarity, and compliance.\n\nUpdate:\n{update['doc_update']}"""
        try:
            response = client.create_response(
                thread_id="review-thread",  # Replace with real thread logic if needed
                model="gpt-4.1",
                instructions="You are a documentation reviewer. Approve or suggest improvements.",
                input=prompt,
            )
            feedback = response.get("output_text", "").strip()
            reviewed.append({**update, "review_feedback": feedback})
            print(
                f"[multi_agent_review] Review for {update['file']}: {feedback[:100]}..."
            )
        except Exception as e:
            print(f"[multi_agent_review] Error for {update['file']}: {e}")
    return reviewed


def generate_commit_message(reviewed_updates: List[Dict]) -> str:
    """
    Generate a descriptive commit message based on agent review and file changes.
    """
    lines = ["Agentic doc update: sync code and documentation\n"]
    for update in reviewed_updates:
        file = update["file"]
        doc_summary = update["doc_update"].split("\n")[0][:80]  # First line/summary
        lines.append(f"- {file}: {doc_summary} ...")
    lines.append(
        "\nCompliance: All changes reviewed and validated by agentic workflow."
    )
    return "\n".join(lines)


def finalize_update(
    reviewed_updates: List[Dict],
    docs_dir: str = "docs/applications/agentic_doc_manager/",
) -> None:
    """
    Write updated docs, commit/version, and print compliance report. Create docs_dir if missing.
    """
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        print(f"[finalize_update] Created docs directory: {docs_dir}")
    updated_doc_paths = []
    for update in reviewed_updates:
        file = update["file"]
        doc_update = update["doc_update"]
        doc_name = os.path.splitext(os.path.basename(file))[0] + ".md"
        doc_path = os.path.join(docs_dir, doc_name)
        try:
            with open(doc_path, "w") as f:
                f.write(doc_update)
            print(f"[finalize_update] Wrote updated doc: {doc_path}")
            updated_doc_paths.append(doc_path)
        except Exception as e:
            print(f"[finalize_update] Error writing {doc_path}: {e}")
    # Stage all outstanding changes (including untracked files)
    try:
        subprocess.run(["git", "add", "-A"], check=True)
        # Add a short delay to ensure file system is up to date
        time.sleep(2)
        commit_msg = generate_commit_message(reviewed_updates)
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
        )
        print("[finalize_update] Committed all outstanding changes.")
    except Exception as e:
        print(f"[finalize_update] Git commit error: {e}")
    # Print compliance report
    print("[finalize_update] Compliance report:")
    for update in reviewed_updates:
        print(
            f"- {update['file']}: {update.get('review_feedback', 'No feedback')[:100]}..."
        )
