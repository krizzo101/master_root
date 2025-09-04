#!/usr/bin/env python3
"""
Unified Monitoring Dashboard - All Phase 1 Completion Monitoring Tools

Provides easy access to all monitoring capabilities for 18 parallel execution
"""
import os
import subprocess
import sys
from pathlib import Path


def print_monitoring_menu():
    """Print the monitoring options menu"""

    print("📊 UNIFIED CONTEXT SYSTEM - MONITORING DASHBOARD")
    print("=" * 60)
    print("   Updated for 18 parallel execution and new orchestrators")
    print()

    print("🔧 AVAILABLE MONITORING TOOLS:")
    print("-" * 30)
    print("   1. Phase 1 Completion Monitor    - Track Phase 1 completion tasks")
    print("   2. Token Usage Monitor           - Monitor 18 token parallel capacity")
    print("   3. Multi-Phase Monitor           - Monitor all phases (updated)")
    print("   4. Session Log Monitor           - Real-time Claude session logs")
    print("   5. Process Monitor               - Active execution processes")
    print("   6. Quick Status Check            - Fast overview")
    print()

    print("🚀 EXECUTION FILES AVAILABLE:")
    print("-" * 30)
    print("   • execute_phase1_generic.py      - GenericOrchestrator (18 parallel)")
    print(
        "   • execute_phase1_practical.py    - PracticalOrchestrator (deterministic UUIDs)"
    )
    print("   • execute_phase1_completion.py   - EnhancedOrchestrator (has issues)")
    print()


def run_monitoring_tool(choice: str):
    """Run the selected monitoring tool"""

    base_dir = Path("/home/opsvi/master_root/apps/project-context")

    tools = {
        "1": ("monitor_phase1_completion.py", "Phase 1 Completion Monitor"),
        "2": ("monitor_token_usage.py", "Token Usage Monitor"),
        "3": ("monitor_multi_phase.py", "Multi-Phase Monitor"),
    }

    if choice in tools:
        script, name = tools[choice]
        script_path = base_dir / script

        if script_path.exists():
            print(f"🚀 Launching {name}...")
            print(f"   Use --watch for continuous monitoring")
            print(f"   Use Ctrl+C to exit")
            print()

            try:
                subprocess.run([sys.executable, str(script_path)], cwd=base_dir)
            except KeyboardInterrupt:
                print(f"\n👋 {name} stopped")
        else:
            print(f"❌ {script} not found at {script_path}")

    elif choice == "4":
        print("📊 REAL-TIME SESSION LOG MONITOR")
        print("-" * 32)
        print("For deterministic session monitoring, use these commands:")
        print()

        tasks = [
            "implement_chat_adapter",
            "implement_code_adapter",
            "integrate_with_mcp",
            "comprehensive_testing",
            "create_documentation",
        ]

        for task in tasks:
            # Generate deterministic UUID (matching PracticalOrchestrator)
            import hashlib

            seed_string = f"practical-{task}-development-specialist"
            hash_obj = hashlib.md5(seed_string.encode())
            hex_str = hash_obj.hexdigest()
            session_id = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

            print(f"   # {task}")
            print(f"   tail -f ~/.claude/projects/*/{session_id}.jsonl")
            print()

    elif choice == "5":
        print("🏃 ACTIVE PROCESS MONITOR")
        print("-" * 22)

        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            found_processes = False
            for line in result.stdout.split("\n"):
                if (
                    any(
                        script in line
                        for script in ["execute_phase1", "monitor_", "python"]
                    )
                    and "project-context" in line
                ):
                    if not found_processes:
                        print("   Active processes:")
                        found_processes = True
                    parts = line.split()
                    if len(parts) >= 11:
                        print(f"   PID {parts[1]}: {parts[10]} (CPU: {parts[2]}%)")

            if not found_processes:
                print("   ⏸️  No active executions detected")

        except Exception as e:
            print(f"   ❌ Error checking processes: {e}")

    elif choice == "6":
        print("⚡ QUICK STATUS CHECK")
        print("-" * 18)

        # Check token configuration
        tokens_file = Path.home() / ".claude" / "tokens.json"
        if tokens_file.exists():
            try:
                import json

                with open(tokens_file) as f:
                    data = json.load(f)
                print(f"   🪙 Tokens configured: {len(data.get('tokens', []))}")
                print(
                    f"   ⚡ Parallel capacity: {data.get('configured_for_parallel', 'unknown')}"
                )
            except:
                print(f"   🪙 Token file exists but couldn't read")
        else:
            print(f"   ❌ No tokens file found")

        # Check for recent output
        output_dirs = [
            "phase1_completion_generic_output",
            "phase1_completion_practical_output",
            "phase1_completion_output",
        ]

        for output_dir in output_dirs:
            dir_path = base_dir / output_dir
            if dir_path.exists():
                tasks_dir = dir_path / "tasks"
                if tasks_dir.exists():
                    task_files = list(tasks_dir.glob("*.json"))
                    print(f"   📁 {output_dir}: {len(task_files)} task outputs")

        # Check Claude session activity
        claude_logs_dir = Path.home() / ".claude" / "projects"
        if claude_logs_dir.exists():
            import time

            cutoff_time = time.time() - (600)  # 10 minutes
            recent_sessions = 0

            try:
                for project_dir in claude_logs_dir.glob("*"):
                    if project_dir.is_dir():
                        for session_file in project_dir.glob("*.jsonl"):
                            if session_file.stat().st_mtime > cutoff_time:
                                recent_sessions += 1

                print(f"   📊 Recent sessions (10min): {recent_sessions}")
            except:
                print(f"   📊 Could not check session activity")

    else:
        print(f"❌ Invalid choice: {choice}")


def main():
    """Main monitoring dashboard interface"""

    print_monitoring_menu()

    while True:
        try:
            choice = (
                input("Select monitoring tool (1-6) or 'q' to quit: ").strip().lower()
            )

            if choice == "q" or choice == "quit":
                print("👋 Goodbye!")
                break

            if choice in ["1", "2", "3", "4", "5", "6"]:
                print()
                run_monitoring_tool(choice)
                print()
                input("Press Enter to return to menu...")
                print()
                print_monitoring_menu()
            else:
                print("❌ Please select 1-6 or 'q' to quit")

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
