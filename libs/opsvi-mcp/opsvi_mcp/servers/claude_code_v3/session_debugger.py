#!/usr/bin/env python3
"""
Agent Session Debugger - Interactive tool for debugging multi-agent executions
Provides deep visibility into what each agent did, why it failed, and how to fix it
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree


class SessionDebugger:
    """Interactive debugger for agent sessions"""

    def __init__(self, session_dir: Path = Path("/tmp/agent_monitoring")):
        self.session_dir = session_dir
        self.console = Console()
        self.sessions: Dict[str, Dict] = {}
        self._load_sessions()

    def _load_sessions(self):
        """Load all available sessions"""
        for agent_dir in self.session_dir.iterdir():
            if agent_dir.is_dir():
                session_file = agent_dir / "session_summary.json"
                if session_file.exists():
                    with open(session_file) as f:
                        self.sessions[agent_dir.name] = json.load(f)

    def list_sessions(self):
        """List all available sessions"""
        table = Table(title="Available Agent Sessions")
        table.add_column("Job ID", style="cyan")
        table.add_column("Phase", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Errors", style="red")

        for job_id, session in self.sessions.items():
            status_icon = "✅" if session.get("status") == "completed" else "❌"
            duration = f"{session.get('duration_seconds', 0):.1f}s"
            error_count = len(session.get("errors", []))

            table.add_row(
                job_id[:16] + "...",
                session.get("phase", "unknown"),
                f"{status_icon} {session.get('status', 'unknown')}",
                duration,
                str(error_count) if error_count > 0 else "-",
            )

        self.console.print(table)

    def debug_session(self, job_id: str):
        """Debug a specific session"""

        # Find matching session
        matching = [jid for jid in self.sessions if job_id in jid]
        if not matching:
            self.console.print(f"[red]Session {job_id} not found[/red]")
            return

        full_job_id = matching[0]
        session = self.sessions[full_job_id]

        # Display session overview
        self.console.print(
            Panel.fit(
                f"[bold cyan]Session Debug: {full_job_id}[/bold cyan]\n"
                f"Phase: {session.get('phase')}\n"
                f"Status: {session.get('status')}\n"
                f"Duration: {session.get('duration_seconds', 0):.1f}s",
                title="Overview",
            )
        )

        # Show validation results
        if "validation" in session:
            self._show_validation_results(session["validation"])

        # Show errors
        if session.get("errors"):
            self._show_errors(session["errors"])

        # Show files created
        if session.get("files_created"):
            self._show_files_created(session["files_created"])

        # Load and show session log
        self._show_session_log(full_job_id)

        # Show health checks
        self._show_health_checks(full_job_id)

        # Provide recommendations
        self._provide_recommendations(session)

    def _show_validation_results(self, validation: Dict):
        """Show validation results"""
        self.console.print("\n[bold yellow]Validation Results:[/bold yellow]")

        passed = validation.get("passed", False)
        status = "[green]PASSED[/green]" if passed else "[red]FAILED[/red]"
        self.console.print(f"Overall: {status}")

        if "checks" in validation:
            for check, result in validation["checks"].items():
                icon = "✅" if result else "❌"
                self.console.print(f"  {icon} {check}")

        if validation.get("errors"):
            self.console.print("\n[red]Validation Errors:[/red]")
            for error in validation["errors"]:
                self.console.print(f"  • {error}")

    def _show_errors(self, errors: List[str]):
        """Show errors encountered"""
        self.console.print("\n[bold red]Errors Encountered:[/bold red]")
        for i, error in enumerate(errors, 1):
            self.console.print(f"  {i}. {error}")

    def _show_files_created(self, files: List[str]):
        """Show files created by agent"""
        self.console.print("\n[bold green]Files Created:[/bold green]")
        for file in files:
            self.console.print(f"  📄 {file}")

    def _show_session_log(self, job_id: str):
        """Show session log with pattern highlighting"""
        session_log = self.session_dir / job_id / "session.jsonl"

        if not session_log.exists():
            return

        self.console.print("\n[bold cyan]Session Log Highlights:[/bold cyan]")

        important_lines = []
        with open(session_log) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    content = entry.get("content", "")

                    # Highlight important patterns
                    if any(
                        pattern in content.lower()
                        for pattern in [
                            "error",
                            "failed",
                            "warning",
                            "creating",
                            "writing",
                            "validating",
                        ]
                    ):
                        important_lines.append(
                            {
                                "line": entry.get("line", 0),
                                "content": content,
                                "metadata": entry.get("parsed", {}),
                            }
                        )
                except:
                    pass

        # Show last 10 important lines
        for entry in important_lines[-10:]:
            # Color code based on content
            if "error" in entry["content"].lower():
                style = "red"
            elif "warning" in entry["content"].lower():
                style = "yellow"
            elif (
                "creating" in entry["content"].lower()
                or "writing" in entry["content"].lower()
            ):
                style = "green"
            else:
                style = "white"

            self.console.print(
                f"  [{entry['line']:4d}] [{style}]{entry['content'][:80]}[/{style}]"
            )

    def _show_health_checks(self, job_id: str):
        """Show health check timeline"""
        health_log = self.session_dir / job_id / "health.json"

        if not health_log.exists():
            return

        with open(health_log) as f:
            health = json.load(f)

        self.console.print("\n[bold magenta]Health Status:[/bold magenta]")
        self.console.print(f"  Status: {health.get('status')}")
        self.console.print(f"  Progress: {health.get('progress', 0)}%")
        self.console.print(
            f"  Current Action: {health.get('current_action', 'Unknown')}"
        )
        self.console.print(f"  Memory Usage: {health.get('memory_mb', 0):.1f} MB")
        self.console.print(f"  Tools Used: {health.get('tools_used_count', 0)}")
        self.console.print(f"  Files Created: {health.get('files_created_count', 0)}")

    def _provide_recommendations(self, session: Dict):
        """Provide recommendations based on session analysis"""
        self.console.print("\n[bold blue]Recommendations:[/bold blue]")

        recommendations = []

        # Check for timeout
        if session.get("status") == "timeout":
            duration = session.get("duration_seconds", 0)
            recommendations.append(
                f"• Agent timed out after {duration:.0f}s. Consider increasing timeout for {session.get('phase')} phase to {duration * 1.5:.0f}s"
            )

        # Check for validation failures
        if session.get("validation", {}).get("passed") == False:
            val_errors = session.get("validation", {}).get("errors", [])
            if "No requirements document created" in str(val_errors):
                recommendations.append(
                    "• Agent failed to create required documents. Check if agent has write permissions and correct output path."
                )
            if "Unresolved errors" in str(val_errors):
                recommendations.append(
                    "• Agent encountered errors but continued. Add error recovery logic or fail-fast behavior."
                )

        # Check for missing files
        if not session.get("files_created"):
            recommendations.append(
                "• No files were created. Verify agent understood the task and had necessary permissions."
            )

        # Check for high error count
        error_count = len(session.get("errors", []))
        if error_count > 5:
            recommendations.append(
                f"• High error count ({error_count}). Review error patterns and add specific error handling."
            )

        if not recommendations:
            recommendations.append(
                "• Session completed successfully. No specific improvements identified."
            )

        for rec in recommendations:
            self.console.print(rec)

    def compare_sessions(self, job_id1: str, job_id2: str):
        """Compare two sessions to identify differences"""

        # Find matching sessions
        matching1 = [jid for jid in self.sessions if job_id1 in jid]
        matching2 = [jid for jid in self.sessions if job_id2 in jid]

        if not matching1 or not matching2:
            self.console.print("[red]One or both sessions not found[/red]")
            return

        session1 = self.sessions[matching1[0]]
        session2 = self.sessions[matching2[0]]

        # Create comparison table
        table = Table(title="Session Comparison")
        table.add_column("Attribute", style="cyan")
        table.add_column(f"Session 1 ({job_id1[:8]})", style="magenta")
        table.add_column(f"Session 2 ({job_id2[:8]})", style="yellow")

        # Compare key attributes
        attributes = [
            ("Phase", "phase"),
            ("Status", "status"),
            ("Duration (s)", "duration_seconds"),
            ("Validation Passed", lambda s: s.get("validation", {}).get("passed")),
            ("Error Count", lambda s: len(s.get("errors", []))),
            ("Files Created", lambda s: len(s.get("files_created", []))),
        ]

        for label, attr in attributes:
            if callable(attr):
                val1 = attr(session1)
                val2 = attr(session2)
            else:
                val1 = session1.get(attr, "N/A")
                val2 = session2.get(attr, "N/A")

            # Format values
            if isinstance(val1, float):
                val1 = f"{val1:.1f}"
            if isinstance(val2, float):
                val2 = f"{val2:.1f}"

            table.add_row(label, str(val1), str(val2))

        self.console.print(table)

    def export_report(self, output_file: Path):
        """Export comprehensive debugging report"""

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_sessions": len(self.sessions),
            "sessions": {},
        }

        for job_id, session in self.sessions.items():
            # Load additional data
            session_dir = self.session_dir / job_id

            session_data = {"summary": session, "logs": [], "health_checks": []}

            # Load session log
            session_log = session_dir / "session.jsonl"
            if session_log.exists():
                with open(session_log) as f:
                    for line in f:
                        try:
                            session_data["logs"].append(json.loads(line))
                        except:
                            pass

            # Load health log
            health_log = session_dir / "health.json"
            if health_log.exists():
                with open(health_log) as f:
                    session_data["health_checks"].append(json.load(f))

            report["sessions"][job_id] = session_data

        # Save report
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        self.console.print(f"[green]Report exported to {output_file}[/green]")


def main():
    """Main entry point for debugger"""
    parser = argparse.ArgumentParser(description="Debug multi-agent SDLC sessions")
    parser.add_argument(
        "--session-dir",
        default="/tmp/agent_monitoring",
        help="Directory containing agent sessions",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available sessions"
    )
    parser.add_argument("--debug", metavar="JOB_ID", help="Debug specific session")
    parser.add_argument(
        "--compare", nargs=2, metavar=("JOB1", "JOB2"), help="Compare two sessions"
    )
    parser.add_argument(
        "--export", metavar="FILE", help="Export debugging report to file"
    )

    args = parser.parse_args()

    debugger = SessionDebugger(Path(args.session_dir))

    if args.list:
        debugger.list_sessions()
    elif args.debug:
        debugger.debug_session(args.debug)
    elif args.compare:
        debugger.compare_sessions(args.compare[0], args.compare[1])
    elif args.export:
        debugger.export_report(Path(args.export))
    else:
        # Interactive mode
        debugger.list_sessions()
        print("\nUse --debug JOB_ID to debug a specific session")


if __name__ == "__main__":
    # Handle missing rich library gracefully
    try:
        main()
    except ImportError:
        print("Note: Install 'rich' library for better visualization: pip install rich")
        print("Falling back to basic output...")

        # Basic implementation without rich
        import json
        from pathlib import Path

        session_dir = Path("/tmp/agent_monitoring")
        if session_dir.exists():
            for agent_dir in session_dir.iterdir():
                if agent_dir.is_dir():
                    summary = agent_dir / "session_summary.json"
                    if summary.exists():
                        with open(summary) as f:
                            data = json.load(f)
                            print(f"\nJob: {agent_dir.name}")
                            print(f"  Phase: {data.get('phase')}")
                            print(f"  Status: {data.get('status')}")
                            print(f"  Duration: {data.get('duration_seconds', 0):.1f}s")
