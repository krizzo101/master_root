import subprocess
import sys

from src.applications.doc_cleanup.doc_cleanup_doc_update import (
    finalize_update,
    multi_agent_review,
    orchestrate_update,
)
from src.applications.doc_cleanup.doc_cleanup_drift_detection import (
    detect_drift,
    monitor_changes,
    trigger_cleanup,
)


def run_doc_cleanup_doc_sync(base_ref="HEAD~1", target_ref="HEAD"):
    print("[workflow_runner] Starting doc_cleanup doc sync workflow...")
    changed_files = monitor_changes(base_ref, target_ref)
    if not changed_files:
        print("[workflow_runner] No changed files detected. Exiting.")
        return
    drift_flags = detect_drift(changed_files)
    if not drift_flags:
        print("[workflow_runner] No documentation drift detected. Exiting.")
        return
    cleanup_tasks = trigger_cleanup(drift_flags)
    doc_update_plan = orchestrate_update(cleanup_tasks)
    reviewed_updates = multi_agent_review(doc_update_plan)
    finalize_update(reviewed_updates)
    print("[workflow_runner] Doc Cleanup doc sync workflow complete.")

    # Automated git commit step
    try:
        # Check if there are staged changes
        status = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
        )
        if status.stdout.strip():
            commit = subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "Doc Cleanup doc update: sync with code changes",
                ],
                capture_output=True,
                text=True,
            )
            print("[workflow_runner] Git commit result:")
            print(commit.stdout or commit.stderr)
        else:
            print("[workflow_runner] No staged changes to commit.")
    except Exception as e:
        print(f"[workflow_runner] Git commit error: {e}")


if __name__ == "__main__":
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1"
    target_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    run_doc_cleanup_doc_sync(base_ref, target_ref)
