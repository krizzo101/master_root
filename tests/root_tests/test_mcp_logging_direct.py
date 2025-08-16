#!/usr/bin/env python3
"""
Direct test of the claude-code MCP server logging through subprocess
"""

import json
import subprocess


def send_mcp_request(request):
    """Send a request to the MCP server via stdin"""
    cmd = ["/home/opsvi/miniconda/bin/python", "-m", "opsvi_mcp.servers.claude_code"]

    # Set up environment with DEBUG logging
    import os

    env = os.environ.copy()
    env["CLAUDE_LOG_LEVEL"] = "DEBUG"
    env["CLAUDE_PERF_LOGGING"] = "true"
    env["CLAUDE_CHILD_LOGGING"] = "true"
    env["CLAUDE_RECURSION_LOGGING"] = "true"
    env["PYTHONPATH"] = "/home/opsvi/master_root/libs"

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Send request
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    # Wait for response (with timeout)
    try:
        stdout, stderr = process.communicate(timeout=10)
        return stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        return None, "Timeout"


def test_logging():
    """Test the MCP server with logging"""
    print("=" * 60)
    print("TESTING CLAUDE-CODE MCP SERVER LOGGING")
    print("=" * 60)

    # Test simple tool call
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "claude_list_jobs", "arguments": {}},
    }

    print("\n[TEST] Calling claude_list_jobs...")
    stdout, stderr = send_mcp_request(request)

    if stderr:
        print("\n[STDERR OUTPUT - This contains our logs]")
        print("-" * 40)
        # Parse and display log entries
        for line in stderr.split("\n"):
            if line.strip():
                print(line)
        print("-" * 40)

    if stdout:
        print("\n[STDOUT OUTPUT - MCP Response]")
        print("-" * 40)
        try:
            # Try to parse and pretty print
            for line in stdout.split("\n"):
                if line.strip():
                    data = json.loads(line)
                    print(json.dumps(data, indent=2))
        except:
            print(stdout)
        print("-" * 40)

    # Check log files
    from pathlib import Path

    log_dir = Path("/home/opsvi/master_root/logs/claude-code")
    if log_dir.exists():
        log_files = sorted(log_dir.glob("parallel-execution-*.log"))
        if log_files:
            latest_log = log_files[-1]
            print(f"\n[LOG FILE] {latest_log.name}")
            print("-" * 40)
            with open(latest_log) as f:
                lines = f.readlines()
                for line in lines[-20:]:  # Show last 20 lines
                    try:
                        entry = json.loads(line)
                        level = entry.get("level", "UNKNOWN")
                        msg = entry.get("message", "")
                        print(f"[{level:8}] {msg}")
                        if entry.get("data"):
                            print(
                                f"           Data: {json.dumps(entry['data'], indent=11)}"
                            )
                    except:
                        pass
            print("-" * 40)


if __name__ == "__main__":
    test_logging()
