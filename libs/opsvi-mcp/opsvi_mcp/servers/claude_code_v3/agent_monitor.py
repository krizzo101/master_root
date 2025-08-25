#!/usr/bin/env python3
"""
Real-time Agent Monitoring and Session Capture
Provides visibility into what agents are doing as they execute
"""

import asyncio
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple


class SessionCaptureAgent:
    """Captures and analyzes agent output in real-time"""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Patterns to detect in output
        self.patterns = {
            "session_id": re.compile(r'session[_-]id["\s:]+([a-f0-9-]{36})'),
            "error": re.compile(r"(?:Error|ERROR|Failed|FAILED|Exception):\s*(.+)"),
            "warning": re.compile(r"(?:Warning|WARNING|Warn|WARN):\s*(.+)"),
            "file_write": re.compile(
                r"(?:Writing|Creating|Saving)\s+(?:to\s+)?([/\w.-]+)"
            ),
            "file_read": re.compile(
                r"(?:Reading|Loading|Opening)\s+(?:from\s+)?([/\w.-]+)"
            ),
            "tool_use": re.compile(r"(?:Using|Calling|Executing)\s+tool:\s*(\w+)"),
            "mcp_server": re.compile(r"MCP\s+server\s+(\w+)\s+(?:started|initialized)"),
            "validation": re.compile(r"Validation:\s*(\w+)"),
            "test_result": re.compile(r"Tests?:\s*(\d+)\s+passed,\s*(\d+)\s+failed"),
            "progress": re.compile(r"Progress:\s*(\d+)%"),
            "phase": re.compile(r"Phase:\s*(\w+)"),
            "status": re.compile(r"Status:\s*(\w+)"),
        }

    async def capture_session_stream(
        self, process: subprocess.Popen, job_id: str, phase: str, timeout: int = 600
    ) -> Dict[str, Any]:
        """Capture agent output stream with real-time analysis"""

        session = {
            "job_id": job_id,
            "phase": phase,
            "started_at": datetime.now().isoformat(),
            "lines": [],
            "errors": [],
            "warnings": [],
            "files_created": [],
            "files_read": [],
            "tools_used": [],
            "mcp_servers": [],
            "status": "running",
            "progress": 0,
            "metrics": {},
        }

        # Create session directory
        session_dir = self.base_dir / phase / job_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Open session log file
        session_log = session_dir / "session.jsonl"
        health_log = session_dir / "health.json"

        start_time = time.time()
        line_count = 0
        last_health_check = time.time()

        try:
            with open(session_log, "w") as log_file:
                while True:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        session["status"] = "timeout"
                        session["error"] = f"Timed out after {timeout} seconds"
                        process.kill()
                        break

                    # Read output line
                    line = process.stdout.readline() if process.stdout else ""

                    if not line:
                        # Check if process has terminated
                        if process.poll() is not None:
                            session["status"] = "completed"
                            session["return_code"] = process.returncode
                            break

                        # Small delay to avoid busy waiting
                        await asyncio.sleep(0.1)
                        continue

                    line = line.strip()
                    if not line:
                        continue

                    line_count += 1

                    # Parse line for patterns
                    parsed = self._parse_line(line, session)

                    # Log entry
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "line": line_count,
                        "content": line,
                        "parsed": parsed,
                    }

                    # Write to JSONL log
                    json.dump(log_entry, log_file)
                    log_file.write("\n")
                    log_file.flush()

                    # Store important lines
                    if parsed:
                        session["lines"].append(log_entry)

                    # Health check every 10 lines
                    if line_count % 10 == 0:
                        health = self._generate_health_status(session, line_count)
                        with open(health_log, "w") as f:
                            json.dump(health, f, indent=2)

                        # Print progress
                        if health.get("progress", 0) > session.get("progress", 0):
                            print(f"   📊 Progress: {health['progress']}%")
                            session["progress"] = health["progress"]

                    # Real-time alerts for errors
                    if parsed and "error" in parsed:
                        print(f"   ❌ Error detected: {parsed['error'][:80]}...")

                    # Track file operations
                    if parsed and "file_write" in parsed:
                        print(f"   📝 Creating: {parsed['file_write']}")

        except Exception as e:
            session["status"] = "error"
            session["error"] = str(e)
            print(f"   ⚠️  Session capture error: {e}")

        finally:
            # Final session summary
            session["ended_at"] = datetime.now().isoformat()
            session["duration_seconds"] = time.time() - start_time
            session["total_lines"] = line_count

            # Save session summary
            summary_file = session_dir / "session_summary.json"
            with open(summary_file, "w") as f:
                json.dump(session, f, indent=2)

            print(f"\n   📁 Session saved: {session_dir}")
            print(f"   ⏱️  Duration: {session['duration_seconds']:.1f}s")
            print(f"   📝 Lines captured: {line_count}")

            if session["errors"]:
                print(f"   ❌ Errors: {len(session['errors'])}")
            if session["files_created"]:
                print(f"   📄 Files created: {len(session['files_created'])}")

        return session

    def _parse_line(self, line: str, session: Dict) -> Dict[str, Any]:
        """Parse a line for known patterns"""
        parsed = {}

        for pattern_name, pattern in self.patterns.items():
            match = pattern.search(line)
            if match:
                value = match.group(1) if match.groups() else True
                parsed[pattern_name] = value

                # Update session state
                if pattern_name == "error":
                    session["errors"].append(value)
                elif pattern_name == "warning":
                    session["warnings"].append(value)
                elif pattern_name == "file_write":
                    if value not in session["files_created"]:
                        session["files_created"].append(value)
                elif pattern_name == "file_read":
                    if value not in session["files_read"]:
                        session["files_read"].append(value)
                elif pattern_name == "tool_use":
                    if value not in session["tools_used"]:
                        session["tools_used"].append(value)
                elif pattern_name == "mcp_server":
                    if value not in session["mcp_servers"]:
                        session["mcp_servers"].append(value)
                elif pattern_name == "progress":
                    session["progress"] = int(value)
                elif pattern_name == "status":
                    session["current_status"] = value

        return parsed

    def _generate_health_status(self, session: Dict, line_count: int) -> Dict[str, Any]:
        """Generate health status for monitoring"""

        # Calculate health metrics
        error_rate = len(session["errors"]) / max(line_count, 1)
        has_progress = session.get("progress", 0) > 0
        has_output = len(session["files_created"]) > 0

        # Determine health status
        if error_rate > 0.1:
            status = "unhealthy"
        elif error_rate > 0.05:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "line_count": line_count,
            "error_count": len(session["errors"]),
            "error_rate": error_rate,
            "progress": session.get("progress", 0),
            "files_created_count": len(session["files_created"]),
            "tools_used_count": len(session["tools_used"]),
            "current_action": session.get("current_status", "processing"),
            "has_progress": has_progress,
            "has_output": has_output,
            "memory_mb": 0,  # Would need psutil to get actual memory
            "cpu_percent": 0,  # Would need psutil to get actual CPU
        }


class PhaseValidator:
    """Validates phase completion and outputs"""

    def __init__(self):
        self.validation_rules = {
            "discovery": self._validate_discovery,
            "design": self._validate_design,
            "planning": self._validate_planning,
            "development": self._validate_development,
            "testing": self._validate_testing,
        }

    async def validate_phase(
        self, phase: str, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate phase outputs and completion"""

        validation = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "checks": {},
            "errors": [],
            "warnings": [],
        }

        # Check session status
        if session.get("status") == "timeout":
            validation["errors"].append(
                f"Phase timed out after {config.get('timeout')}s"
            )
            validation["checks"]["completed"] = False
        elif session.get("status") == "error":
            validation["errors"].append(
                f"Phase failed with error: {session.get('error')}"
            )
            validation["checks"]["completed"] = False
        else:
            validation["checks"]["completed"] = True

        # Check for errors in output
        if session.get("errors"):
            validation["errors"].append(
                f"Found {len(session['errors'])} errors in output"
            )
            validation["warnings"].append("Errors detected but phase continued")
            validation["checks"]["no_errors"] = False
        else:
            validation["checks"]["no_errors"] = True

        # Check required outputs
        required_outputs = config.get("required_outputs", [])
        for output in required_outputs:
            output_path = project_path / output
            if output_path.exists() or any(
                f.endswith(output) for f in session.get("files_created", [])
            ):
                validation["checks"][f"has_{output}"] = True
            else:
                validation["checks"][f"has_{output}"] = False
                validation["errors"].append(f"Required output missing: {output}")

        # Run phase-specific validation
        if phase in self.validation_rules:
            phase_validation = await self.validation_rules[phase](
                project_path, session, config
            )
            validation["checks"].update(phase_validation.get("checks", {}))
            validation["errors"].extend(phase_validation.get("errors", []))

        # Determine overall pass/fail
        validation["passed"] = (
            validation["checks"].get("completed", False)
            and all(v for k, v in validation["checks"].items() if k.startswith("has_"))
            and len(validation["errors"]) == 0
        )

        return validation

    async def _validate_discovery(
        self, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate discovery phase outputs"""
        return {
            "checks": {
                "requirements_documented": (project_path / "requirements.md").exists(),
                "scope_defined": any(
                    "scope" in f.lower() for f in session.get("files_created", [])
                ),
                "constraints_identified": True,  # Could check content
            },
            "errors": [],
        }

    async def _validate_design(
        self, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate design phase outputs"""
        return {
            "checks": {
                "architecture_defined": (project_path / "architecture.md").exists(),
                "interfaces_specified": any(
                    "api" in f.lower() for f in session.get("files_created", [])
                ),
                "data_models_created": True,  # Could check for schema files
            },
            "errors": [],
        }

    async def _validate_planning(
        self, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate planning phase outputs"""
        tasks_file = project_path / "tasks.json"
        checks = {"tasks_defined": tasks_file.exists()}
        errors = []

        if tasks_file.exists():
            try:
                with open(tasks_file) as f:
                    tasks = json.load(f)
                    checks["dependencies_mapped"] = any(
                        "depends_on" in t for t in tasks
                    )
                    checks["timeline_created"] = any("duration" in t for t in tasks)
            except:
                errors.append("tasks.json is not valid JSON")

        return {"checks": checks, "errors": errors}

    async def _validate_development(
        self, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate development phase outputs"""
        return {
            "checks": {
                "code_implemented": (project_path / "src").exists()
                or any("src/" in f for f in session.get("files_created", [])),
                "no_syntax_errors": len(
                    [e for e in session.get("errors", []) if "syntax" in e.lower()]
                )
                == 0,
                "dependencies_resolved": True,  # Could check package files
            },
            "errors": [],
        }

    async def _validate_testing(
        self, project_path: Path, session: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Validate testing phase outputs"""
        return {
            "checks": {
                "tests_created": (project_path / "tests").exists()
                or any("test" in f for f in session.get("files_created", [])),
                "tests_passing": "failed"
                not in " ".join(session.get("errors", [])).lower(),
                "coverage_adequate": True,  # Would need to parse coverage report
            },
            "errors": [],
        }


class AgentHealthMonitor:
    """Monitor agent health and performance"""

    async def check_health(self, session: Dict) -> Dict[str, Any]:
        """Generate health report for agent session"""

        health = {
            "status": "unknown",
            "metrics": {},
            "issues": [],
            "recommendations": [],
        }

        # Analyze session metrics
        duration = session.get("duration_seconds", 0)
        errors = len(session.get("errors", []))
        files_created = len(session.get("files_created", []))
        lines = session.get("total_lines", 0)

        health["metrics"] = {
            "duration_seconds": duration,
            "error_count": errors,
            "files_created": files_created,
            "lines_processed": lines,
            "error_rate": errors / max(lines, 1),
            "productivity_rate": files_created
            / max(duration / 60, 1),  # files per minute
        }

        # Determine health status
        if session.get("status") == "timeout":
            health["status"] = "timeout"
            health["issues"].append("Agent exceeded time limit")
            health["recommendations"].append(f"Increase timeout beyond {duration}s")
        elif errors > 10:
            health["status"] = "unhealthy"
            health["issues"].append(f"High error count: {errors}")
            health["recommendations"].append(
                "Review error patterns and add error handling"
            )
        elif errors > 5:
            health["status"] = "degraded"
            health["issues"].append(f"Moderate error count: {errors}")
        elif session.get("status") == "completed":
            health["status"] = "healthy"
        else:
            health["status"] = session.get("status", "unknown")

        # Additional recommendations
        if files_created == 0:
            health["recommendations"].append(
                "No files created - verify agent understood task"
            )

        if duration > 900:  # 15 minutes
            health["recommendations"].append(
                "Consider breaking task into smaller phases"
            )

        return health


class MonitoringDashboard:
    """Live monitoring dashboard for multi-agent execution"""

    def __init__(self):
        self.dashboard_file = Path("/tmp/agent_monitoring/dashboard/status.json")
        self.dashboard_file.parent.mkdir(parents=True, exist_ok=True)
        self.status = {}

    async def initialize(self, project_name: str, phases: List):
        """Initialize dashboard for project"""
        self.status = {
            "project": project_name,
            "started_at": datetime.now().isoformat(),
            "phases": {phase.value: {"status": "pending"} for phase in phases},
            "total_agents": 0,
            "active_agents": 0,
            "completed_agents": 0,
            "failed_agents": 0,
        }
        self._save()

    async def update_phase_status(self, phase: str, status: str, details: Dict):
        """Update phase status in dashboard"""
        self.status["phases"][phase] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "duration": details.get("duration_seconds"),
            "validation_passed": details.get("validation", {}).get("passed"),
            "errors": len(details.get("validation", {}).get("errors", [])),
        }

        # Update counters
        self.status["total_agents"] += 1
        if status == "completed":
            self.status["completed_agents"] += 1
        elif status == "failed":
            self.status["failed_agents"] += 1

        self._save()

    def _save(self):
        """Save dashboard state"""
        with open(self.dashboard_file, "w") as f:
            json.dump(self.status, f, indent=2)
