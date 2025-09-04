#!/usr/bin/env python3
"""
Multi-Phase Execution Monitor for Unified Context System
Real-time tracking of Phase 1, 2, 3+ execution progress with optimization analytics
"""
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MultiPhaseMonitor:
    """Monitor execution across multiple phases with deterministic session ID tracking"""

    def __init__(self):
        self.base_dir = Path("/home/opsvi/master_root/apps/project-context")

        # Updated to include new execution methods and 18 parallel support
        self.phase_dirs = {
            "phase1": self.base_dir / "phase1_execution_output",
            "phase1_generic": self.base_dir / "phase1_completion_generic_output",
            "phase1_practical": self.base_dir / "phase1_completion_practical_output",
            "phase1_completion": self.base_dir / "phase1_completion_output",
            "phase2": self.base_dir / "phase2_execution_output",
            "phase3": self.base_dir / "phase3_execution_output",
        }
        self.claude_logs_dir = Path.home() / ".claude" / "projects"

        # Track maximum parallel execution (updated for 18 parallel)
        self.max_parallel_capacity = 18

    def generate_deterministic_session_id(
        self, task_id: str, plan_id: str = "unified_context"
    ) -> str:
        """Generate deterministic session ID matching ExecutionPlanAdapter logic"""
        import hashlib

        seed_string = f"{plan_id}-{task_id}"
        hash_obj = hashlib.md5(seed_string.encode())
        hex_str = hash_obj.hexdigest()
        # Format as proper UUID
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    def get_session_logs(self, session_id: str) -> Optional[List[Dict]]:
        """Get Claude session logs for a specific session ID"""
        try:
            # Search all project directories for the session log file
            for project_dir in self.claude_logs_dir.glob("*"):
                if project_dir.is_dir():
                    session_file = project_dir / f"{session_id}.jsonl"
                    if session_file.exists():
                        logs = []
                        with open(session_file, "r") as f:
                            for line in f:
                                if line.strip():
                                    logs.append(json.loads(line))
                        return logs
            return None
        except Exception as e:
            print(f"Error reading session logs for {session_id}: {e}")
            return None

    def get_phase_status(self, phase: str) -> Dict:
        """Get detailed status for a specific phase"""
        phase_dir = self.phase_dirs.get(phase)
        if not phase_dir or not phase_dir.exists():
            return {
                "phase": phase,
                "status": "not_started",
                "tasks": [],
                "summary": {"total": 0, "completed": 0, "active": 0, "failed": 0},
            }

        tasks_dir = phase_dir / "tasks"
        sessions_dir = phase_dir / "sessions"

        if not tasks_dir.exists():
            return {
                "phase": phase,
                "status": "not_started",
                "tasks": [],
                "summary": {"total": 0, "completed": 0, "active": 0, "failed": 0},
            }

        # Analyze task outputs
        tasks = []
        task_files = list(tasks_dir.glob("*.json"))

        for task_file in task_files:
            try:
                with open(task_file, "r") as f:
                    task_data = json.load(f)

                tasks.append(
                    {
                        "task_id": task_file.stem,
                        "agent_type": task_data.get("agent_type", "unknown"),
                        "status": task_data.get("status", "unknown"),
                        "start_time": task_data.get("start_time"),
                        "end_time": task_data.get("end_time"),
                        "duration": task_data.get("execution_time_seconds", 0),
                        "output_size": len(str(task_data.get("content", ""))),
                    }
                )
            except Exception as e:
                tasks.append(
                    {"task_id": task_file.stem, "status": "error", "error": str(e)}
                )

        # Calculate summary statistics
        summary = {
            "total": len(tasks),
            "completed": len([t for t in tasks if t.get("status") == "completed"]),
            "active": len(
                [t for t in tasks if t.get("status") in ["running", "in_progress"]]
            ),
            "failed": len([t for t in tasks if t.get("status") in ["failed", "error"]]),
        }

        # Determine overall phase status
        if summary["total"] == 0:
            status = "not_started"
        elif summary["active"] > 0:
            status = "running"
        elif summary["failed"] > summary["completed"]:
            status = "failed"
        elif summary["completed"] == summary["total"]:
            status = "completed"
        else:
            status = "partial"

        return {
            "phase": phase,
            "status": status,
            "tasks": tasks,
            "summary": summary,
            "last_updated": datetime.now().isoformat(),
        }

    def get_execution_analytics(self) -> Dict:
        """Get cross-phase execution analytics"""
        analytics = {
            "execution_efficiency": {},
            "parallel_utilization": {},
            "agent_performance": {},
            "bottleneck_analysis": {},
            "optimization_opportunities": [],
        }

        all_tasks = []
        for phase in ["phase1", "phase2", "phase3"]:
            phase_status = self.get_phase_status(phase)
            all_tasks.extend([(phase, task) for task in phase_status["tasks"]])

        if not all_tasks:
            return analytics

        # Execution efficiency analysis
        completed_tasks = [
            (phase, task)
            for phase, task in all_tasks
            if task.get("status") == "completed" and task.get("duration")
        ]

        if completed_tasks:
            durations = [task["duration"] for _, task in completed_tasks]
            analytics["execution_efficiency"] = {
                "avg_task_duration": sum(durations) / len(durations),
                "total_execution_time": sum(durations),
                "fastest_task": min(durations),
                "slowest_task": max(durations),
                "completed_count": len(completed_tasks),
            }

        # Agent performance analysis
        agent_stats = {}
        for phase, task in completed_tasks:
            agent_type = task.get("agent_type", "unknown")
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {
                    "count": 0,
                    "total_duration": 0,
                    "phases": set(),
                }

            agent_stats[agent_type]["count"] += 1
            agent_stats[agent_type]["total_duration"] += task.get("duration", 0)
            agent_stats[agent_type]["phases"].add(phase)

        analytics["agent_performance"] = {
            agent: {
                "task_count": stats["count"],
                "avg_duration": stats["total_duration"] / stats["count"]
                if stats["count"] > 0
                else 0,
                "phases_used": list(stats["phases"]),
            }
            for agent, stats in agent_stats.items()
        }

        # Optimization opportunities
        if analytics["execution_efficiency"]:
            avg_duration = analytics["execution_efficiency"]["avg_task_duration"]
            slow_tasks = [
                task
                for _, task in completed_tasks
                if task["duration"] > avg_duration * 1.5
            ]

            if slow_tasks:
                analytics["optimization_opportunities"].append(
                    {
                        "type": "slow_tasks",
                        "count": len(slow_tasks),
                        "recommendation": "Consider breaking down or optimizing slow tasks",
                    }
                )

        # Parallelization analysis
        phase_summaries = [
            self.get_phase_status(phase)["summary"]
            for phase in ["phase1", "phase2", "phase3"]
        ]
        total_tasks = sum(s["total"] for s in phase_summaries)
        if total_tasks > 4:  # More tasks than available tokens
            analytics["optimization_opportunities"].append(
                {
                    "type": "token_utilization",
                    "current_tokens": 4,
                    "total_tasks": total_tasks,
                    "recommendation": "Consider increasing token pool for higher parallelization",
                }
            )

        return analytics

    def print_comprehensive_status(self):
        """Print comprehensive multi-phase status report"""
        print("🔍 UNIFIED CONTEXT SYSTEM - MULTI-PHASE EXECUTION MONITOR")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Phase-by-phase status
        for phase in ["phase1", "phase2", "phase3"]:
            status = self.get_phase_status(phase)
            summary = status["summary"]

            status_emoji = {
                "completed": "✅",
                "running": "🔄",
                "partial": "⚠️",
                "failed": "❌",
                "not_started": "⏳",
            }.get(status["status"], "❓")

            print(
                f"{status_emoji} PHASE {phase.upper()[-1]} - {status['status'].upper()}"
            )
            print(f"   Tasks: {summary['completed']}/{summary['total']} completed")
            if summary["active"] > 0:
                print(f"   Active: {summary['active']} running")
            if summary["failed"] > 0:
                print(f"   Failed: {summary['failed']} tasks")

            # Show recent task completions
            completed_tasks = [
                t for t in status["tasks"] if t.get("status") == "completed"
            ]
            if completed_tasks:
                recent_tasks = sorted(
                    completed_tasks, key=lambda x: x.get("end_time", ""), reverse=True
                )[:3]
                for task in recent_tasks:
                    duration = task.get("duration", 0)
                    print(
                        f"     ✅ {task['task_id']} ({task.get('agent_type', 'unknown')}) - {duration:.1f}s"
                    )
            print()

        # Execution Analytics
        analytics = self.get_execution_analytics()

        if analytics["execution_efficiency"]:
            eff = analytics["execution_efficiency"]
            print("📊 EXECUTION ANALYTICS")
            print(f"   Average Task Duration: {eff['avg_task_duration']:.1f}s")
            print(f"   Total Execution Time: {eff['total_execution_time']:.1f}s")
            print(f"   Completed Tasks: {eff['completed_count']}")
            print(
                f"   Performance Range: {eff['fastest_task']:.1f}s - {eff['slowest_task']:.1f}s"
            )
            print()

        # Agent Performance
        if analytics["agent_performance"]:
            print("🤖 AGENT PERFORMANCE")
            agent_perf = analytics["agent_performance"]
            sorted_agents = sorted(
                agent_perf.items(), key=lambda x: x[1]["task_count"], reverse=True
            )[:5]

            for agent, stats in sorted_agents:
                print(
                    f"   {agent}: {stats['task_count']} tasks, {stats['avg_duration']:.1f}s avg"
                )
            print()

        # Optimization Opportunities
        if analytics["optimization_opportunities"]:
            print("⚡ OPTIMIZATION OPPORTUNITIES")
            for opp in analytics["optimization_opportunities"]:
                print(f"   {opp['type']}: {opp['recommendation']}")
            print()

        # System Status
        print("🎯 SYSTEM STATUS")
        all_phases = [
            self.get_phase_status(phase) for phase in ["phase1", "phase2", "phase3"]
        ]
        total_completed = sum(p["summary"]["completed"] for p in all_phases)
        total_tasks = sum(p["summary"]["total"] for p in all_phases)
        active_tasks = sum(p["summary"]["active"] for p in all_phases)

        if total_tasks > 0:
            completion_rate = (total_completed / total_tasks) * 100
            print(
                f"   Overall Progress: {total_completed}/{total_tasks} tasks ({completion_rate:.1f}%)"
            )

        if active_tasks > 0:
            print(f"   Active Execution: {active_tasks} tasks running")
            print("   🔄 System is actively executing tasks")
        elif total_completed == total_tasks and total_tasks > 0:
            print("   🎉 All phases completed successfully!")
        else:
            print("   ⏳ System ready for next phase execution")

        print()

        # Session ID monitoring info
        print("🎯 SESSION MONITORING")
        print("   Deterministic session IDs enabled for easy log tracking")
        print("   Task → Session ID mapping:")
        sample_tasks = [
            "implement_base_pipeline",
            "implement_chat_adapter",
            "research_cicd_integration",
        ]
        for task in sample_tasks:
            session_id = self.generate_deterministic_session_id(task)
            print(f"     {task} → {session_id}")
        print("   Monitor with: tail -f ~/.claude/projects/*/[session-id].jsonl")

        print()
        print("💡 Use 'python execute_phase2_optimized.py' to start Phase 2")
        print("💡 Use 'python execute_phase3_optimized.py' to start Phase 3")
        print("💡 Use 'python monitor_multi_phase.py --watch' for live monitoring")


def main():
    """Main monitoring function"""
    monitor = MultiPhaseMonitor()

    # Check if continuous monitoring is requested
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--watch":
        print("🔍 Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                os.system("clear" if os.name == "posix" else "cls")  # Clear screen
                monitor.print_comprehensive_status()
                time.sleep(10)  # Update every 10 seconds
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped.")
    else:
        monitor.print_comprehensive_status()


if __name__ == "__main__":
    main()
