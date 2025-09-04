#!/usr/bin/env python3
"""
Complete Chat Log PostgreSQL Import - Master Orchestrator
Execute all 3 phases with comprehensive monitoring and validation
"""
import asyncio
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")


async def execute_phase(phase_num: int, phase_name: str, script_name: str):
    """Execute a single phase and return results"""

    print(f"\n🚀 PHASE {phase_num}: {phase_name}")
    print(f"=" * 60)
    print(f"📄 Executing: {script_name}")

    start_time = time.time()

    # Import and run the phase script
    try:
        if phase_num == 1:
            from execute_chat_import_phase1 import main as phase1_main

            result = await phase1_main()
        elif phase_num == 2:
            from execute_chat_import_phase2 import main as phase2_main

            result = await phase2_main()
        elif phase_num == 3:
            from execute_chat_import_production import main as phase3_main

            result = await phase3_main()
        else:
            raise ValueError(f"Unknown phase: {phase_num}")

        end_time = time.time()
        duration = end_time - start_time

        if result == 0:
            print(f"✅ PHASE {phase_num} COMPLETED in {duration:.1f}s - {phase_name}")
            return True
        else:
            print(f"❌ PHASE {phase_num} FAILED after {duration:.1f}s - {phase_name}")
            return False

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ PHASE {phase_num} ERROR after {duration:.1f}s - {phase_name}: {e}")
        return False


async def main():
    """Execute complete chat log PostgreSQL import across all phases"""

    # Check if running in background (no TTY)
    import sys

    background_mode = not sys.stdout.isatty()

    if background_mode:
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting chat import in background mode"
        )
    else:
        print("🎯 CHAT LOG POSTGRESQL IMPORT - COMPLETE ORCHESTRATION")
        print("=" * 80)
        print("📊 Data Volume: 133MB SQLite → PostgreSQL")
        print("📋 Records: 539 sessions, 41,137 messages, 19,847 tool calls")
        print("⚡ Execution: 18 parallel agents across 3 phases")
        print("🎯 Goal: Production-ready chat analytics system")
        print()

    total_start_time = time.time()

    # Phase definitions
    phases = [
        (1, "Infrastructure Setup", "execute_chat_import_phase1.py"),
        (2, "Data Processing", "execute_chat_import_phase2.py"),
        (3, "Production Execution", "execute_chat_import_production.py"),
    ]

    results = []

    # Execute each phase sequentially
    for phase_num, phase_name, script_name in phases:
        success = await execute_phase(phase_num, phase_name, script_name)
        results.append((phase_num, phase_name, success))

        if not success:
            print(f"\n💥 EXECUTION HALTED: Phase {phase_num} failed")
            print("🔧 Please review errors and re-run individual phase if needed")
            break

        # Brief pause between phases
        if phase_num < 3:
            print(f"⏸️  Brief pause before Phase {phase_num + 1}...")
            await asyncio.sleep(2)

    # Final summary
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time

    print(f"\n🎯 COMPLETE CHAT LOG IMPORT - FINAL RESULTS")
    print(f"=" * 80)

    successful_phases = [r for r in results if r[2]]
    failed_phases = [r for r in results if not r[2]]

    print(
        f"⏱️  Total Execution Time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)"
    )
    print(f"✅ Successful Phases: {len(successful_phases)}/3")
    print(f"❌ Failed Phases: {len(failed_phases)}/3")
    print()

    for phase_num, phase_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} Phase {phase_num}: {phase_name}")

    if len(successful_phases) == 3:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print(f"🚀 Chat Log PostgreSQL Import FULLY OPERATIONAL")
        print(f"📊 System ready for:")
        print(f"   • Chat search and analytics")
        print(f"   • Conversation flow analysis")
        print(f"   • Tool usage tracking")
        print(f"   • Agent performance monitoring")
        print(f"   • File operation analysis")
        print(f"📈 Next steps:")
        print(f"   • Access chat analytics via unified context API")
        print(f"   • Use chat search tools with PostgreSQL backend")
        print(f"   • Monitor system performance and usage")
        return 0
    else:
        print(f"\n⚠️  PARTIAL COMPLETION")
        print(f"🔧 Successful phases can be used independently")
        print(f"🔄 Failed phases can be re-executed individually:")
        for phase_num, phase_name, success in failed_phases:
            print(f"   python execute_chat_import_phase{phase_num}.py")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
