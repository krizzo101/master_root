#!/usr/bin/env python3
"""
Script to run handoff analysis on the top 20 largest chat log files
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Top 20 largest log files (in order of size)
LOG_FILES = [
    "chat_logs/d76456f5-2d29-4c42-9ede-ed13f7a2a4b7.jsonl",  # 10.5MB
    "chat_logs/5bf5f085-53bd-4bab-8245-721e417e94e3.jsonl",  # 10.2MB
    "chat_logs/6010818e-35cb-47d9-b33b-82cac9fc64bd.jsonl",  # 8.6MB
    "chat_logs/f4edd35a-86d5-413d-8f1d-574901a391e0.jsonl",  # 8.5MB
    "chat_logs/2fbc3aaf-4365-4155-a59a-3b95c18959f0.jsonl",  # 8.1MB
    "chat_logs/c0846985-c066-4293-867a-1af7a50b7984.jsonl",  # 7.5MB
    "chat_logs/10c67da3-2884-4fad-b47a-58a1b3e8552c.jsonl",  # 7.5MB
    "chat_logs/7696db5c-cd72-452c-9bda-e11c60ffd2c5.jsonl",  # 7.5MB
    "chat_logs/1fd265db-dd7a-4482-acaf-872d4a0e19c1.jsonl",  # 6.6MB
    "chat_logs/b21f3bba-20a2-4b9a-b2ee-e0999091dc4b.jsonl",  # 6.0MB
    "chat_logs/02b2cf03-1acb-4916-85d3-b4b81338ec19.jsonl",  # 6.0MB
    "chat_logs/b0075c2f-7577-4836-8085-2de3a6b6dd75.jsonl",  # 5.9MB
    "chat_logs/d08fb6a3-6638-403b-8a61-4ec04b44a6bd.jsonl",  # 5.4MB
    "chat_logs/476b169b-a894-4063-aab2-27fa42e7fc58.jsonl",  # 5.2MB
    "chat_logs/efeb8086-e7c2-4a55-af31-cf4f0e4dd73c.jsonl",  # 5.1MB
    "chat_logs/61f069d4-a6d3-4e7e-894b-87aab6e35602.jsonl",  # 5.0MB
    "chat_logs/3b080dd8-c621-4452-9ae3-60aca752bbb5.jsonl",  # 4.9MB
    "chat_logs/14d10927-6718-41a7-a183-328c5aba1a5e.jsonl",  # 4.6MB
    "chat_logs/b14a02d2-0336-4e1a-8fb4-7c2944060e91.jsonl",  # 4.6MB
    "chat_logs/76586d9b-d166-4c7b-8c9b-103ea8a18052.jsonl",  # 4.4MB
]


def run_handoff_command(log_file):
    """Run handoff command on a single log file"""
    try:
        # Check if file exists
        if not os.path.exists(log_file):
            return {"file": log_file, "status": "error", "error": "File not found"}

        # Extract session ID from filename (remove .jsonl extension)
        session_id = Path(log_file).stem

        # Run handoff command
        result = subprocess.run(
            ["python", ".claude/commands/handoff.py", session_id],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per file
            cwd="/home/opsvi/master_root",
        )

        return {
            "file": log_file,
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "file": log_file,
            "status": "timeout",
            "error": "Command timed out after 5 minutes",
        }
    except FileNotFoundError:
        return {
            "file": log_file,
            "status": "error",
            "error": "handoff script not found",
        }
    except Exception as e:
        return {"file": log_file, "status": "error", "error": str(e)}


def main():
    """Main execution function"""
    print(f"Starting handoff analysis on {len(LOG_FILES)} files at {datetime.now()}")

    results = []

    for i, log_file in enumerate(LOG_FILES, 1):
        print(f"Processing {i}/{len(LOG_FILES)}: {log_file}")

        result = run_handoff_command(log_file)
        results.append(result)

        # Print immediate status
        if result["status"] == "success":
            print(f"  ✓ Success")
        elif result["status"] == "error":
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
        elif result["status"] == "timeout":
            print(f"  ⏱ Timeout")

    # Save results to JSON file
    output_file = (
        f"handoff_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_files": len(LOG_FILES),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\nAnalysis complete! Results saved to: {output_file}")

    # Summary statistics
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    timeout_count = sum(1 for r in results if r["status"] == "timeout")

    print(f"Summary:")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"  ⏱ Timeouts: {timeout_count}")

    # Show successful outputs
    if success_count > 0:
        print(f"\nSuccessful handoff outputs:")
        for result in results:
            if result["status"] == "success" and result["stdout"]:
                print(f"\n--- {result['file']} ---")
                print(
                    result["stdout"][:500] + "..."
                    if len(result["stdout"]) > 500
                    else result["stdout"]
                )


if __name__ == "__main__":
    main()
