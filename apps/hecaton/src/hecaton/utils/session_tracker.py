"""
Session Tracker for HECATON
Tracks Claude agent sessions with UUID correlation and audit trail
"""

import json
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionTracker:
    """Tracks all Claude agent sessions with full audit capabilities"""

    def __init__(self, base_log_dir: str = "/home/opsvi/master_root/apps/hecaton/logs"):
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(exist_ok=True)

        # Session tracking
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_log_file = (
            self.base_log_dir / f"session_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        )

        # Component correlation
        self.correlation_map: Dict[str, List[str]] = {}

        # Initialize tracking file
        self._write_event(
            {
                "event": "SESSION_TRACKER_INIT",
                "timestamp": datetime.now().isoformat(),
                "log_file": str(self.session_log_file),
            }
        )

    def create_agent_session(self, agent_id: str, agent_type: str, task: str) -> str:
        """Create a new agent session with UUID"""
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "task": task,
            "created_at": datetime.now().isoformat(),
            "status": "INITIALIZED",
            "claude_log_path": None,
            "events": [],
        }

        self.sessions[session_id] = session_data

        # Map agent_id to session_id for correlation
        if agent_id not in self.correlation_map:
            self.correlation_map[agent_id] = []
        self.correlation_map[agent_id].append(session_id)

        self._write_event(
            {
                "event": "AGENT_SESSION_CREATED",
                "timestamp": datetime.now().isoformat(),
                **session_data,
            }
        )

        return session_id

    def track_claude_execution(self, session_id: str, command: List[str], worktree_path: str):
        """Track Claude CLI execution with session ID"""
        if session_id not in self.sessions:
            return

        # Extract session ID from command if present
        claude_session_id = None
        for i, arg in enumerate(command):
            if arg == "--session-id" and i + 1 < len(command):
                claude_session_id = command[i + 1]
                break

        # If no session ID in command, add one
        if not claude_session_id:
            claude_session_id = session_id
            command.extend(["--session-id", claude_session_id])

        # Determine log path
        claude_log_path = (
            Path.home()
            / ".claude"
            / "projects"
            / Path(worktree_path).name
            / f"{claude_session_id}.jsonl"
        )

        event = {
            "event": "CLAUDE_EXECUTION_START",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "claude_session_id": claude_session_id,
            "command": " ".join(command),
            "worktree_path": worktree_path,
            "claude_log_path": str(claude_log_path),
        }

        self.sessions[session_id]["claude_log_path"] = str(claude_log_path)
        self.sessions[session_id]["status"] = "EXECUTING"
        self.sessions[session_id]["events"].append(event)

        self._write_event(event)

    def track_execution_complete(self, session_id: str, result: Dict[str, Any], duration_ms: int):
        """Track completion of Claude execution"""
        if session_id not in self.sessions:
            return

        event = {
            "event": "CLAUDE_EXECUTION_COMPLETE",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "duration_ms": duration_ms,
            "success": result.get("success", False),
            "result_summary": str(result.get("output", ""))[:500],  # First 500 chars
        }

        self.sessions[session_id]["status"] = "COMPLETED" if result.get("success") else "FAILED"
        self.sessions[session_id]["events"].append(event)

        self._write_event(event)

        # Try to extract metrics from Claude session
        self._extract_claude_metrics(session_id)

    def track_component_event(self, component: str, event_type: str, details: Dict[str, Any]):
        """Track events from any component"""
        event = {
            "event": "COMPONENT_EVENT",
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "event_type": event_type,
            **details,
        }

        self._write_event(event)

    def get_session_audit_trail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full audit trail for a session"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # Try to read Claude session log if available
        claude_log_contents = None
        if session.get("claude_log_path") and Path(session["claude_log_path"]).exists():
            try:
                with open(session["claude_log_path"], "r") as f:
                    claude_log_contents = [json.loads(line) for line in f]
            except Exception as e:
                claude_log_contents = f"Error reading log: {e}"

        return {
            **session,
            "claude_log_contents": claude_log_contents,
            "correlation": {
                "agent_id": session["agent_id"],
                "related_sessions": self.correlation_map.get(session["agent_id"], []),
            },
        }

    def get_realtime_status(self) -> Dict[str, Any]:
        """Get real-time status of all components"""
        active_sessions = [s for s in self.sessions.values() if s["status"] == "EXECUTING"]
        completed_sessions = [s for s in self.sessions.values() if s["status"] == "COMPLETED"]
        failed_sessions = [s for s in self.sessions.values() if s["status"] == "FAILED"]

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(self.sessions),
                "active": len(active_sessions),
                "completed": len(completed_sessions),
                "failed": len(failed_sessions),
            },
            "active_sessions": active_sessions,
            "recent_completions": completed_sessions[-5:] if completed_sessions else [],
            "recent_failures": failed_sessions[-5:] if failed_sessions else [],
        }

    def _extract_claude_metrics(self, session_id: str):
        """Extract metrics from Claude session log"""
        session = self.sessions.get(session_id)
        if not session or not session.get("claude_log_path"):
            return

        log_path = Path(session["claude_log_path"])
        if not log_path.exists():
            return

        try:
            metrics = {"total_messages": 0, "tool_uses": 0, "tokens_used": 0, "errors": 0}

            with open(log_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "message":
                            metrics["total_messages"] += 1
                        elif entry.get("type") == "tool_use":
                            metrics["tool_uses"] += 1
                        elif entry.get("type") == "error":
                            metrics["errors"] += 1
                        # Extract token usage if available
                        if "usage" in entry:
                            metrics["tokens_used"] += entry["usage"].get("total_tokens", 0)
                    except:
                        continue

            self.sessions[session_id]["metrics"] = metrics

            self._write_event(
                {
                    "event": "METRICS_EXTRACTED",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    **metrics,
                }
            )

        except Exception as e:
            self.track_component_event(
                "SessionTracker",
                "METRICS_EXTRACTION_ERROR",
                {"session_id": session_id, "error": str(e)},
            )

    def _write_event(self, event: Dict[str, Any]):
        """Write event to session tracking log"""
        try:
            with open(self.session_log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"Error writing session event: {e}")

    def generate_correlation_report(self) -> str:
        """Generate a correlation report showing relationships between components"""
        report = ["=" * 80]
        report.append("HECATON SESSION CORRELATION REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        status = self.get_realtime_status()
        report.append(f"Total Sessions: {status['summary']['total_sessions']}")
        report.append(f"Active: {status['summary']['active']}")
        report.append(f"Completed: {status['summary']['completed']}")
        report.append(f"Failed: {status['summary']['failed']}")
        report.append("")

        # Agent correlation
        report.append("AGENT CORRELATIONS")
        report.append("-" * 40)
        for agent_id, session_ids in self.correlation_map.items():
            report.append(f"\nAgent: {agent_id}")
            for sid in session_ids:
                session = self.sessions.get(sid)
                if session:
                    report.append(
                        f"  └─ Session {sid[:8]}... | Type: {session['agent_type']} | Status: {session['status']}"
                    )
                    if session.get("metrics"):
                        m = session["metrics"]
                        report.append(
                            f"     Metrics: {m['tool_uses']} tools, {m['tokens_used']} tokens"
                        )

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)
