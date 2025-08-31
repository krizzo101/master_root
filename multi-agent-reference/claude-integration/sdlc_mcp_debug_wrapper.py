#!/usr/bin/env python3
"""
SDLC MCP Debug Wrapper
Captures comprehensive debug information from every claude-code MCP execution
"""

import json
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path


class SDLCDebugWrapper:
    def __init__(self, phase, project_path, log_dir=None):
        self.phase = phase
        self.project_path = Path(project_path)
        self.log_dir = Path(log_dir or "/home/opsvi/master_root/.sdlc-logs")
        self.log_dir.mkdir(exist_ok=True)

        # Create timestamped log files
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log = self.log_dir / f"{phase}_{self.timestamp}_execution.json"
        self.debug_log = self.log_dir / f"{phase}_{self.timestamp}_debug.log"
        self.state_log = self.log_dir / f"{phase}_{self.timestamp}_state.json"

        # Track execution state
        self.execution_data = {
            "phase": phase,
            "project": str(project_path),
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "errors": [],
            "files_created": [],
            "files_modified": [],
            "tools_used": [],
        }

        self.log_step("INIT", f"Debug wrapper initialized for {phase} phase")

    def log_step(self, step_type, message, data=None):
        """Log a step with timestamp and optional data"""
        timestamp = datetime.now().isoformat()

        # Console output
        print(f"[{timestamp}] [{step_type}] {message}")

        # Debug log (human readable)
        with open(self.debug_log, "a") as f:
            f.write(f"[{timestamp}] [{step_type}] {message}\n")
            if data:
                f.write(f"  Data: {json.dumps(data, indent=2)}\n")

        # Execution log (structured JSON)
        step_entry = {
            "timestamp": timestamp,
            "type": step_type,
            "message": message,
            "data": data,
        }
        self.execution_data["steps"].append(step_entry)

        # Write execution data after each step
        with open(self.execution_log, "w") as f:
            json.dump(self.execution_data, f, indent=2)

    def capture_state(self, label):
        """Capture current state of project directory"""
        state = {"label": label, "timestamp": datetime.now().isoformat(), "files": {}}

        # Capture file structure
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.project_path)
                state["files"][str(rel_path)] = {
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }

        # Capture git status
        try:
            git_status = subprocess.check_output(
                ["git", "status", "--short"], cwd=self.project_path, text=True
            )
            state["git_status"] = git_status
        except Exception:
            state["git_status"] = "Unable to get git status"

        # Save state
        with open(self.state_log, "w") as f:
            json.dump(state, f, indent=2)

        self.log_step("STATE", f"Captured state: {label}", state)
        return state

    def execute_mcp_call(self, task_description):
        """
        Execute the actual MCP call with comprehensive logging
        This is where we would integrate with the real MCP client
        """
        self.log_step("MCP_CALL_START", "Initiating MCP claude-code call")

        # Capture pre-execution state
        pre_state = self.capture_state("pre-execution")

        try:
            # Log the exact task being sent
            self.log_step(
                "MCP_TASK",
                "Task description",
                {
                    "task": task_description,
                    "phase": self.phase,
                    "project": str(self.project_path),
                },
            )

            # Here's where the actual MCP call would go
            # For now, we're showing the structure
            mcp_params = {
                "task": task_description,
                "outputFormat": "json",
                "permissionMode": "bypassPermissions",
                "verbose": True,  # Request verbose output
            }

            self.log_step("MCP_PARAMS", "MCP call parameters", mcp_params)

            # Simulate tracking MCP execution
            # In reality, we'd capture the actual MCP response
            result = {
                "status": "success",
                "message": "This is where MCP execution would happen",
                "duration": 0,
            }

            self.log_step("MCP_RESULT", "MCP execution result", result)

        except Exception as e:
            error_data = {"error": str(e), "traceback": traceback.format_exc()}
            self.execution_data["errors"].append(error_data)
            self.log_step("ERROR", f"MCP execution failed: {e}", error_data)
            raise

        finally:
            # Always capture post-execution state
            post_state = self.capture_state("post-execution")

            # Identify changes
            self.identify_changes(pre_state, post_state)

    def identify_changes(self, pre_state, post_state):
        """Identify what changed during execution"""
        pre_files = set(pre_state.get("files", {}).keys())
        post_files = set(post_state.get("files", {}).keys())

        # New files
        new_files = post_files - pre_files
        if new_files:
            self.execution_data["files_created"] = list(new_files)
            self.log_step(
                "FILES_CREATED", f"Created {len(new_files)} files", list(new_files)
            )

        # Modified files
        modified = []
        for file in pre_files & post_files:
            if (
                pre_state["files"][file]["modified"]
                != post_state["files"][file]["modified"]
            ):
                modified.append(file)

        if modified:
            self.execution_data["files_modified"] = modified
            self.log_step("FILES_MODIFIED", f"Modified {len(modified)} files", modified)

    def finalize(self):
        """Finalize logging and create summary"""
        self.execution_data["end_time"] = datetime.now().isoformat()

        # Create summary
        summary = {
            "phase": self.phase,
            "project": str(self.project_path),
            "start": self.execution_data["start_time"],
            "end": self.execution_data["end_time"],
            "steps_count": len(self.execution_data["steps"]),
            "errors_count": len(self.execution_data["errors"]),
            "files_created": len(self.execution_data["files_created"]),
            "files_modified": len(self.execution_data["files_modified"]),
            "logs": {
                "execution": str(self.execution_log),
                "debug": str(self.debug_log),
                "state": str(self.state_log),
            },
        }

        # Save summary
        summary_file = self.log_dir / f"{self.phase}_{self.timestamp}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        self.log_step("COMPLETE", "Execution complete", summary)

        # Print summary to console
        print("\n" + "=" * 60)
        print(f"PHASE EXECUTION COMPLETE: {self.phase}")
        print("=" * 60)
        print(f"Steps executed: {summary['steps_count']}")
        print(f"Errors: {summary['errors_count']}")
        print(f"Files created: {summary['files_created']}")
        print(f"Files modified: {summary['files_modified']}")
        print("\nLogs saved to:")
        print(f"  - Execution: {self.execution_log}")
        print(f"  - Debug: {self.debug_log}")
        print(f"  - State: {self.state_log}")
        print(f"  - Summary: {summary_file}")
        print("=" * 60)


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python sdlc_mcp_debug_wrapper.py <phase> <project_path> <task_description>"
        )
        sys.exit(1)

    phase = sys.argv[1]
    project_path = sys.argv[2]
    task_description = sys.argv[3]

    wrapper = SDLCDebugWrapper(phase, project_path)

    try:
        wrapper.execute_mcp_call(task_description)
    except Exception as e:
        print(f"Execution failed: {e}")
        sys.exit(1)
    finally:
        wrapper.finalize()


if __name__ == "__main__":
    main()
