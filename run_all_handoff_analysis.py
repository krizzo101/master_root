#!/usr/bin/env python3
"""
Script to run handoff analysis on ALL .jsonl files in chat_logs/ directory
Processing 851 chat log files
"""

import glob
import json
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Thread-safe printing
print_lock = threading.Lock()


def safe_print(message):
    """Thread-safe printing"""
    with print_lock:
        print(message)


def run_handoff_command(log_file, file_index, total_files):
    """Run handoff command on a single log file"""
    try:
        # Check if file exists
        if not os.path.exists(log_file):
            return {
                "file": log_file,
                "index": file_index,
                "status": "error",
                "error": "File not found",
            }

        # Get file size for context
        file_size = os.path.getsize(log_file)

        # Extract session ID from filename (remove .jsonl extension)
        session_id = Path(log_file).stem

        safe_print(
            f"[{file_index:3d}/{total_files}] Processing {session_id} ({file_size:,} bytes)"
        )

        # Run handoff command
        result = subprocess.run(
            ["python", ".claude/commands/handoff.py", session_id],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout per file
            cwd="/home/opsvi/master_root",
        )

        return {
            "file": log_file,
            "session_id": session_id,
            "index": file_index,
            "file_size": file_size,
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "file": log_file,
            "session_id": Path(log_file).stem,
            "index": file_index,
            "status": "timeout",
            "error": "Command timed out after 2 minutes",
        }
    except FileNotFoundError:
        return {
            "file": log_file,
            "session_id": Path(log_file).stem,
            "index": file_index,
            "status": "error",
            "error": "handoff script not found",
        }
    except Exception as e:
        return {
            "file": log_file,
            "session_id": Path(log_file).stem,
            "index": file_index,
            "status": "error",
            "error": str(e),
        }


def analyze_handoff_output(stdout):
    """Extract key information from handoff output"""
    if not stdout:
        return {}

    analysis = {
        "has_handoff_markers": False,
        "has_todo_usage": False,
        "has_tool_usage": False,
        "has_knowledge_context": False,
        "session_scope_found": False,
    }

    # Check for various patterns
    if "HANDOFF_READY:" in stdout or "BLOCKED_ON:" in stdout:
        analysis["has_handoff_markers"] = True

    if "TodoWrite" in stdout or "todo" in stdout.lower():
        analysis["has_todo_usage"] = True

    if "tool_use" in stdout or "Read.*file_path" in stdout:
        analysis["has_tool_usage"] = True

    if "understood" in stdout or "learned" in stdout or "architecture" in stdout:
        analysis["has_knowledge_context"] = True

    if "SESSION SCOPE" in stdout:
        analysis["session_scope_found"] = True

    return analysis


def main():
    """Main execution function"""
    safe_print(f"Starting comprehensive handoff analysis at {datetime.now()}")

    # Get all .jsonl files
    log_files = sorted(glob.glob("chat_logs/*.jsonl"))
    total_files = len(log_files)

    safe_print(f"Found {total_files} .jsonl files to process")

    results = []
    successful_analyses = []

    # Use ThreadPoolExecutor for parallel processing
    max_workers = 8  # Adjust based on system capacity

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_file = {
            executor.submit(run_handoff_command, log_file, i + 1, total_files): (
                log_file,
                i + 1,
            )
            for i, log_file in enumerate(log_files)
        }

        # Process completed jobs
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                results.append(result)

                # Analyze successful outputs
                if result["status"] == "success" and result["stdout"]:
                    analysis = analyze_handoff_output(result["stdout"])
                    result["analysis"] = analysis
                    successful_analyses.append(result)

                # Print status
                status_icon = (
                    "✓"
                    if result["status"] == "success"
                    else ("⏱" if result["status"] == "timeout" else "✗")
                )
                safe_print(
                    f"  {status_icon} [{result['index']:3d}] {result.get('session_id', 'unknown')}"
                )

            except Exception as e:
                safe_print(f"  ✗ Error processing future: {e}")

    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"complete_handoff_analysis_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_files": len(log_files),
                "results": results,
            },
            f,
            indent=2,
        )

    safe_print(f"\nAnalysis complete! Results saved to: {output_file}")

    # Generate comprehensive summary
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    timeout_count = sum(1 for r in results if r["status"] == "timeout")

    safe_print(f"\n{'='*60}")
    safe_print(f"COMPREHENSIVE HANDOFF ANALYSIS SUMMARY")
    safe_print(f"{'='*60}")
    safe_print(f"Total Files Processed: {total_files}")
    safe_print(
        f"  ✓ Successful: {success_count} ({success_count/total_files*100:.1f}%)"
    )
    safe_print(f"  ✗ Errors: {error_count} ({error_count/total_files*100:.1f}%)")
    safe_print(f"  ⏱ Timeouts: {timeout_count} ({timeout_count/total_files*100:.1f}%)")

    if successful_analyses:
        safe_print(f"\nPATTERN ANALYSIS:")
        handoff_markers = sum(
            1
            for r in successful_analyses
            if r.get("analysis", {}).get("has_handoff_markers", False)
        )
        todo_usage = sum(
            1
            for r in successful_analyses
            if r.get("analysis", {}).get("has_todo_usage", False)
        )
        tool_usage = sum(
            1
            for r in successful_analyses
            if r.get("analysis", {}).get("has_tool_usage", False)
        )
        knowledge_context = sum(
            1
            for r in successful_analyses
            if r.get("analysis", {}).get("has_knowledge_context", False)
        )

        safe_print(
            f"  Sessions with handoff markers: {handoff_markers} ({handoff_markers/success_count*100:.1f}%)"
        )
        safe_print(
            f"  Sessions with todo usage: {todo_usage} ({todo_usage/success_count*100:.1f}%)"
        )
        safe_print(
            f"  Sessions with tool usage: {tool_usage} ({tool_usage/success_count*100:.1f}%)"
        )
        safe_print(
            f"  Sessions with knowledge context: {knowledge_context} ({knowledge_context/success_count*100:.1f}%)"
        )

        # File size analysis
        total_bytes = sum(r.get("file_size", 0) for r in successful_analyses)
        avg_size = total_bytes / len(successful_analyses) if successful_analyses else 0
        safe_print(f"\nDATA VOLUME ANALYSIS:")
        safe_print(
            f"  Total data processed: {total_bytes:,} bytes ({total_bytes/1024/1024:.1f} MB)"
        )
        safe_print(
            f"  Average file size: {avg_size:,.0f} bytes ({avg_size/1024:.1f} KB)"
        )

    # Create summary knowledge entry
    summary_output_file = f"handoff_analysis_summary_{timestamp}.json"
    summary_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_files_analyzed": total_files,
        "success_rate": f"{success_count/total_files*100:.1f}%",
        "total_data_volume_mb": round(
            sum(r.get("file_size", 0) for r in results) / 1024 / 1024, 2
        ),
        "pattern_analysis": {
            "handoff_markers_percentage": f"{handoff_markers/success_count*100:.1f}%"
            if success_count > 0
            else "0%",
            "todo_usage_percentage": f"{todo_usage/success_count*100:.1f}%"
            if success_count > 0
            else "0%",
            "tool_usage_percentage": f"{tool_usage/success_count*100:.1f}%"
            if success_count > 0
            else "0%",
            "knowledge_context_percentage": f"{knowledge_context/success_count*100:.1f}%"
            if success_count > 0
            else "0%",
        },
    }

    with open(summary_output_file, "w") as f:
        json.dump(summary_data, f, indent=2)

    safe_print(f"\nSummary saved to: {summary_output_file}")


if __name__ == "__main__":
    main()
