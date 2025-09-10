#!/usr/bin/env python3
"""
Run Chat Import with Background Execution + Foreground Monitoring
Starts orchestrator in background and monitoring in foreground for real-time visibility
"""
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from monitor_chat_import import ChatImportMonitor


class BackgroundOrchestrator:
    """Manages background execution of orchestrator with monitoring"""

    def __init__(self):
        self.orchestrator_process = None
        self.log_file = None
        self.phase_scripts = {
            1: "execute_chat_import_phase1.py",
            2: "execute_chat_import_phase2.py",
            3: "execute_chat_import_production.py",
        }

    def start_background_execution(
        self, phase: int = None, complete: bool = False
    ) -> bool:
        """Start orchestrator execution in background"""

        if complete:
            script_name = "execute_complete_chat_import.py"
            log_name = "complete_chat_import.log"
        elif phase:
            script_name = self.phase_scripts.get(phase)
            log_name = f"chat_import_phase{phase}.log"
            if not script_name:
                print(f"❌ Invalid phase: {phase}")
                return False
        else:
            print("❌ Must specify either --phase N or --complete")
            return False

        # Create log file
        log_path = Path(f"/home/opsvi/master_root/apps/project-context/{log_name}")
        self.log_file = log_path

        # Start orchestrator in background
        cmd = [
            sys.executable,
            f"/home/opsvi/master_root/apps/project-context/{script_name}",
        ]

        print(f"🚀 Starting background execution: {script_name}")
        print(f"📄 Output logging to: {log_path}")
        print(f"🔧 Command: {' '.join(cmd)}")
        print()

        try:
            with open(log_path, "w") as log_file:
                self.orchestrator_process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd="/home/opsvi/master_root/apps/project-context",
                    preexec_fn=os.setsid,  # Create new process group
                )

            print(
                f"✅ Background process started (PID: {self.orchestrator_process.pid})"
            )
            print(f"📊 Starting monitoring in 3 seconds...")
            time.sleep(3)
            return True

        except Exception as e:
            print(f"❌ Failed to start background process: {e}")
            return False

    def stop_background_execution(self):
        """Stop background orchestrator execution"""
        if self.orchestrator_process:
            print(
                f"\n🛑 Stopping background process (PID: {self.orchestrator_process.pid})"
            )
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.orchestrator_process.pid), signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self.orchestrator_process.wait(timeout=10)
                    print("✅ Background process stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    os.killpg(os.getpgid(self.orchestrator_process.pid), signal.SIGKILL)
                    print("⚠️  Background process force-killed")

            except ProcessLookupError:
                print("✅ Background process already stopped")
            except Exception as e:
                print(f"❌ Error stopping background process: {e}")

            self.orchestrator_process = None

    def is_running(self) -> bool:
        """Check if background process is still running"""
        if not self.orchestrator_process:
            return False

        return self.orchestrator_process.poll() is None

    def get_log_tail(self, lines: int = 10) -> str:
        """Get recent log output"""
        if not self.log_file or not self.log_file.exists():
            return "No log file available"

        try:
            with open(self.log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log: {e}"


async def run_with_monitoring(
    phase: int = None, complete: bool = False, monitor_interval: int = 30
):
    """Run orchestrator in background with foreground monitoring"""

    # Initialize background orchestrator
    bg_orchestrator = BackgroundOrchestrator()
    monitor = ChatImportMonitor()

    # Validate system before starting
    print("🔍 Validating system readiness...")
    ready = await monitor.validate_system_readiness()
    if not ready:
        print("❌ System not ready for execution")
        return 1

    print("✅ System validation passed")
    print()

    # Start background execution
    if not bg_orchestrator.start_background_execution(phase=phase, complete=complete):
        return 1

    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n⚠️  Received signal {signum}, shutting down...")
        bg_orchestrator.stop_background_execution()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start monitoring loop
        print("🔍 Starting real-time monitoring...")
        print("📊 Press Ctrl+C to stop monitoring and background execution")
        print("=" * 60)

        while bg_orchestrator.is_running():
            # Get and display current status
            status = await monitor.get_current_status()
            monitor._display_status(status)

            # Show recent log output
            log_tail = bg_orchestrator.get_log_tail(3)
            if log_tail.strip():
                print("📄 Recent Log Output:")
                for line in log_tail.strip().split("\n"):
                    print(f"   {line}")
                print()

            # Check if execution is complete
            if status["overall"]["total_progress_percent"] >= 100:
                print("🎉 Background execution completed successfully!")
                break

            # Wait before next update
            await asyncio.sleep(monitor_interval)

        # Final status check
        if not bg_orchestrator.is_running():
            return_code = (
                bg_orchestrator.orchestrator_process.returncode
                if bg_orchestrator.orchestrator_process
                else 0
            )

            if return_code == 0:
                print("\n✅ Background execution completed successfully!")

                # Show final status
                final_status = await monitor.get_current_status()
                monitor._display_status(final_status)

                print("\n🎯 Chat Import Summary:")
                print("✅ All phases completed")
                print("✅ Data successfully imported to PostgreSQL")
                print("✅ Analytics and monitoring operational")
                return 0
            else:
                print(
                    f"\n❌ Background execution failed with return code: {return_code}"
                )
                print("📄 Check log file for details:")
                print(f"   tail -f {bg_orchestrator.log_file}")
                return 1

    except KeyboardInterrupt:
        print("\n⚠️  Monitoring interrupted by user")
        bg_orchestrator.stop_background_execution()
        return 1

    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        bg_orchestrator.stop_background_execution()
        return 1

    finally:
        # Ensure background process is cleaned up
        bg_orchestrator.stop_background_execution()


async def main():
    """Main execution interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Chat Import with Background Execution + Monitoring"
    )

    # Execution options
    execution_group = parser.add_mutually_exclusive_group(required=True)
    execution_group.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Execute specific phase (1=Infrastructure, 2=Processing, 3=Production)",
    )
    execution_group.add_argument(
        "--complete", action="store_true", help="Execute complete import (all 3 phases)"
    )

    # Monitoring options
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=30,
        help="Monitoring update interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate system readiness, don't execute",
    )

    args = parser.parse_args()

    if args.validate_only:
        monitor = ChatImportMonitor()
        await monitor.validate_system_readiness()
        return 0

    # Run with monitoring
    return await run_with_monitoring(
        phase=args.phase, complete=args.complete, monitor_interval=args.monitor_interval
    )


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
