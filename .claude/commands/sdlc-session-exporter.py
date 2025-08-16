#!/usr/bin/env python3
"""
SDLC Session Exporter - Captures full claude-code execution sessions
Uses multiple methods to ensure complete session capture
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class SDLCSessionExporter:
    """Manages session export for SDLC phase executions."""

    def __init__(self, export_dir: Optional[Path] = None):
        """Initialize session exporter."""
        self.export_dir = Path(export_dir or "/home/opsvi/master_root/.sdlc-sessions")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def execute_with_export(
        self, phase: str, task: str, timeout: int = 1200
    ) -> Dict[str, Any]:
        """
        Execute claude-code with full session export.

        Args:
            phase: SDLC phase name
            task: Task description for claude-code
            timeout: Timeout in seconds

        Returns:
            Dictionary with execution results and session data
        """
        session_file = self.export_dir / f"{phase}_{self.timestamp}_session.json"
        log_file = self.export_dir / f"{phase}_{self.timestamp}_execution.log"

        print(f"Executing {phase} phase with session export...")
        print(f"Session will be saved to: {session_file}")

        # Method 1: Use claude CLI with JSON export
        cmd = [
            "claude",
            task,
            "--output-format",
            "json",
            "--verbose",
            "--print",  # Non-interactive mode
            "--max-thinking-time",
            str(timeout),
        ]

        try:
            # Execute with full output capture
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            # Parse JSON output
            if result.stdout:
                try:
                    session_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If not valid JSON, save raw output
                    session_data = {
                        "raw_output": result.stdout,
                        "error_output": result.stderr,
                        "return_code": result.returncode,
                    }
            else:
                session_data = {
                    "error": "No output received",
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                }

            # Enhance with metadata
            session_data["metadata"] = {
                "phase": phase,
                "timestamp": self.timestamp,
                "timeout": timeout,
                "command": " ".join(cmd),
                "execution_time": datetime.now().isoformat(),
            }

            # Save session data
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            # Save execution log
            with open(log_file, "w") as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Return Code: {result.returncode}\n")
                f.write("\n--- STDOUT ---\n")
                f.write(result.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)

            print(f"Session exported successfully to {session_file}")
            return session_data

        except subprocess.TimeoutExpired:
            error_data = {
                "error": "Execution timeout",
                "phase": phase,
                "timeout": timeout,
                "timestamp": self.timestamp,
            }

            with open(session_file, "w") as f:
                json.dump(error_data, f, indent=2)

            print(f"Execution timed out after {timeout} seconds")
            return error_data

        except Exception as e:
            error_data = {"error": str(e), "phase": phase, "timestamp": self.timestamp}

            with open(session_file, "w") as f:
                json.dump(error_data, f, indent=2)

            print(f"Error during execution: {e}")
            return error_data

    def export_current_session(self) -> Optional[Path]:
        """
        Export the current active session if available.

        Returns:
            Path to exported session file
        """
        # Check for session environment variable
        session_path = os.environ.get("CLAUDE_SESSION_PATH")

        if session_path and Path(session_path).exists():
            export_file = self.export_dir / f"current_{self.timestamp}_session.json"

            with open(session_path, "r") as src:
                session_data = json.load(src)

            # Add export metadata
            session_data["export_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "source_path": session_path,
            }

            with open(export_file, "w") as dst:
                json.dump(session_data, dst, indent=2)

            print(f"Current session exported to: {export_file}")
            return export_file

        return None

    def create_summary_report(self) -> Path:
        """
        Create a summary report of all exported sessions.

        Returns:
            Path to summary report
        """
        summary_file = self.export_dir / f"summary_{self.timestamp}.md"
        sessions = list(self.export_dir.glob("*_session.json"))

        with open(summary_file, "w") as f:
            f.write("# SDLC Session Export Summary\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"Total Sessions: {len(sessions)}\n\n")

            for session_file in sorted(sessions):
                try:
                    with open(session_file, "r") as sf:
                        data = json.load(sf)

                    f.write(f"## {session_file.name}\n")

                    if "metadata" in data:
                        meta = data["metadata"]
                        f.write(f"- Phase: {meta.get('phase', 'unknown')}\n")
                        f.write(f"- Timestamp: {meta.get('timestamp', 'unknown')}\n")
                        f.write(f"- Timeout: {meta.get('timeout', 'unknown')}s\n")

                    if "error" in data:
                        f.write(f"- Status: ERROR - {data['error']}\n")
                    else:
                        f.write("- Status: SUCCESS\n")

                    f.write("\n")

                except Exception as e:
                    f.write(f"- Error reading session: {e}\n\n")

        print(f"Summary report created: {summary_file}")
        return summary_file


def main():
    """Main entry point for session exporter."""
    if len(sys.argv) < 3:
        print("Usage: python sdlc-session-exporter.py <phase> <task>")
        print(
            "Example: python sdlc-session-exporter.py discovery 'Execute discovery phase'"
        )
        sys.exit(1)

    phase = sys.argv[1]
    task = sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 1200

    exporter = SDLCSessionExporter()

    # Execute with export
    result = exporter.execute_with_export(phase, task, timeout)

    # Try to export current session
    exporter.export_current_session()

    # Create summary
    exporter.create_summary_report()

    # Return success/failure based on result
    if "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
