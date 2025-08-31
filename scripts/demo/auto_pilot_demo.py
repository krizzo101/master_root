#!/usr/bin/env python3
"""
Auto-Pilot Demo - Comprehensive demonstration of multi-agent monitoring
Shows all capabilities without requiring actual Claude CLI authentication
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code_v3.agent_monitor import (
    SessionCaptureAgent,
    PhaseValidator,
    AgentHealthMonitor,
    MonitoringDashboard
)


class AutoPilotDemo:
    """Demonstrates all monitoring capabilities"""
    
    def __init__(self):
        self.demo_dir = Path("/tmp/autopilot_demo")
        self.demo_dir.mkdir(exist_ok=True)
        self.session_dir = self.demo_dir / ".sessions"
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize monitoring components
        self.capture = SessionCaptureAgent(self.session_dir)
        self.validator = PhaseValidator()
        self.health = AgentHealthMonitor()
        self.dashboard = MonitoringDashboard()
    
    async def create_mock_agent(self, name: str, phase: str, success: bool = True):
        """Create a mock agent that simulates real agent output"""
        
        script_path = self.demo_dir / f"mock_{name}.sh"
        script_content = f"""#!/bin/bash
echo "Starting {phase} phase for {name}..."
echo "Session ID: mock-{name}-$(date +%s)"
echo "Progress: 10%"
echo "Reading project requirements..."
sleep 0.5
echo "Progress: 30%"
echo "Analyzing codebase..."
echo "Using tool: Read"
echo "Reading from /project/requirements.md"
sleep 0.5
echo "Progress: 50%"
"""
        
        if success:
            script_content += f"""
echo "Creating {phase}/output.md"
echo "Writing to {phase}/output.md"
echo "Progress: 70%"
echo "Running validation checks..."
echo "Validation: passed"
echo "Progress: 90%"
echo "Status: completed"
echo "Progress: 100%"
echo "✅ {phase} phase completed successfully"
"""
        else:
            script_content += f"""
echo "Error: Failed to process requirements"
echo "Warning: Missing configuration"
echo "Progress: 60%"
echo "Attempting recovery..."
sleep 0.5
echo "Error: Recovery failed - timeout"
echo "Status: failed"
echo "❌ {phase} phase failed"
"""
        
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return script_path
    
    async def run_demo_phase(self, phase: str, success: bool = True):
        """Run a demo phase with monitoring"""
        
        print(f"\n{'='*60}")
        print(f"DEMO: {phase.upper()} PHASE")
        print(f"{'='*60}")
        
        # Create mock agent
        agent_script = await self.create_mock_agent(f"agent_{phase}", phase, success)
        
        # Run with monitoring
        process = subprocess.Popen(
            [str(agent_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        job_id = f"demo_{phase}_{int(time.time())}"
        
        # Capture session
        print(f"🎬 Capturing session for {phase}...")
        session = await self.capture.capture_session_stream(
            process=process,
            job_id=job_id,
            phase=phase,
            timeout=10
        )
        
        # Validate
        print(f"\n✅ Validating {phase} outputs...")
        validation = await self.validator.validate_phase(
            phase=phase,
            project_path=self.demo_dir,
            session=session,
            config={
                "required_outputs": [f"{phase}/output.md"],
                "timeout": 10
            }
        )
        
        # Health check
        print(f"🏥 Running health check...")
        health = await self.health.check_health(session)
        
        # Display results
        print(f"\n📊 Results for {phase}:")
        print(f"   Status: {session.get('status', 'unknown')}")
        print(f"   Duration: {session.get('duration_seconds', 0):.1f}s")
        print(f"   Lines captured: {session.get('total_lines', 0)}")
        print(f"   Errors: {len(session.get('errors', []))}")
        print(f"   Files created: {session.get('files_created', [])}")
        print(f"   Validation: {'✅ PASSED' if validation.get('passed') else '❌ FAILED'}")
        print(f"   Health: {health.get('status', 'unknown')}")
        
        if health.get('recommendations'):
            print(f"   Recommendations:")
            for rec in health['recommendations']:
                print(f"      - {rec}")
        
        return {
            "phase": phase,
            "session": session,
            "validation": validation,
            "health": health
        }
    
    async def demonstrate_parallel_execution(self):
        """Demonstrate parallel agent execution"""
        
        print(f"\n{'='*60}")
        print(f"DEMO: PARALLEL AGENT EXECUTION")
        print(f"{'='*60}")
        
        tasks = [
            ("security_scan", "Scanning for vulnerabilities"),
            ("code_quality", "Analyzing code quality"),
            ("documentation", "Checking documentation")
        ]
        
        print(f"\n🚀 Spawning {len(tasks)} parallel agents...")
        
        parallel_scripts = []
        for task_id, task_desc in tasks:
            script = await self.create_mock_agent(task_id, "analysis", success=(task_id != "code_quality"))
            parallel_scripts.append((task_id, script, task_desc))
        
        # Run all in parallel
        processes = []
        for task_id, script, desc in parallel_scripts:
            print(f"   ▶️  Starting: {desc}")
            process = subprocess.Popen(
                [str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append((task_id, process, desc))
        
        # Monitor all
        results = []
        for task_id, process, desc in processes:
            session = await self.capture.capture_session_stream(
                process=process,
                job_id=f"parallel_{task_id}",
                phase="parallel",
                timeout=5
            )
            
            status_icon = "✅" if session.get('status') == 'completed' else "❌"
            print(f"   {status_icon} {desc}: {session.get('status', 'unknown')}")
            results.append(session)
        
        print(f"\n📊 Parallel Execution Summary:")
        print(f"   Total tasks: {len(tasks)}")
        print(f"   Successful: {sum(1 for r in results if r.get('status') == 'completed')}")
        print(f"   Failed: {sum(1 for r in results if r.get('status') != 'completed')}")
        
        return results
    
    async def demonstrate_debugging(self):
        """Demonstrate debugging capabilities"""
        
        print(f"\n{'='*60}")
        print(f"DEMO: SESSION DEBUGGING")
        print(f"{'='*60}")
        
        # Create a failing agent
        print("\n🐛 Creating a failing agent to debug...")
        fail_result = await self.run_demo_phase("debugging", success=False)
        
        # Analyze the failure
        session = fail_result["session"]
        health = fail_result["health"]
        
        print(f"\n🔍 Debugging Analysis:")
        print(f"   Session ID: {session.get('job_id')}")
        print(f"   Status: {session.get('status')}")
        print(f"   Errors found: {len(session.get('errors', []))}")
        
        if session.get('errors'):
            print(f"\n   Error Details:")
            for i, error in enumerate(session.get('errors', [])[:3], 1):
                print(f"   {i}. {error}")
        
        if health.get('recommendations'):
            print(f"\n   📝 Automated Recommendations:")
            for rec in health['recommendations']:
                print(f"   • {rec}")
        
        # Generate debug report
        debug_report = {
            "session_id": session.get('job_id'),
            "failure_analysis": {
                "primary_cause": session.get('errors', ['Unknown'])[0] if session.get('errors') else "Unknown",
                "contributing_factors": session.get('warnings', []),
                "timeline": {
                    "started": session.get('started_at'),
                    "failed": session.get('ended_at'),
                    "duration": session.get('duration_seconds')
                }
            },
            "recovery_plan": health.get('recommendations', []),
            "session_location": str(self.session_dir / session.get('job_id', 'unknown'))
        }
        
        debug_file = self.demo_dir / "debug_report.json"
        with open(debug_file, 'w') as f:
            json.dump(debug_report, f, indent=2)
        
        print(f"\n   📁 Debug report saved: {debug_file}")
        
        return debug_report
    
    async def run_full_demo(self):
        """Run complete auto-pilot demonstration"""
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║         AUTO-PILOT DEMONSTRATION                            ║
║     Multi-Agent Monitoring System in Action                 ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Initialize dashboard (expects SDLCPhase enums, but we'll use strings)
        # Skip dashboard initialization since it expects enums
        
        results = {
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "parallel_execution": None,
            "debugging": None
        }
        
        # 1. Run SDLC phases
        print("\n📋 PART 1: SDLC Phase Execution with Monitoring")
        print("-" * 60)
        
        for phase in ["discovery", "design", "development"]:
            result = await self.run_demo_phase(phase, success=(phase != "design"))
            results["phases"][phase] = result
            
            # Skip dashboard update since we didn't initialize it
            
            await asyncio.sleep(1)  # Brief pause between phases
        
        # 2. Parallel execution
        print("\n📋 PART 2: Parallel Agent Execution")
        print("-" * 60)
        results["parallel_execution"] = await self.demonstrate_parallel_execution()
        
        # 3. Debugging demonstration
        print("\n📋 PART 3: Failure Analysis & Debugging")
        print("-" * 60)
        results["debugging"] = await self.demonstrate_debugging()
        
        # Generate final report
        results["completed_at"] = datetime.now().isoformat()
        
        # Calculate metrics
        total_sessions = len(results["phases"]) + len(results["parallel_execution"]) + 1
        successful = sum(1 for p in results["phases"].values() if p["validation"]["passed"])
        successful += sum(1 for s in results["parallel_execution"] if s.get("status") == "completed")
        
        print(f"\n{'='*60}")
        print(f"AUTO-PILOT DEMONSTRATION COMPLETE")
        print(f"{'='*60}")
        print(f"\n📊 Final Metrics:")
        print(f"   Total agents run: {total_sessions}")
        print(f"   Success rate: {(successful/total_sessions)*100:.1f}%")
        print(f"   Sessions captured: {total_sessions}")
        print(f"   Validation gates: {len(results['phases'])}")
        print(f"   Parallel tasks: {len(results['parallel_execution'])}")
        print(f"   Debug reports: 1")
        
        print(f"\n📁 All session data saved to: {self.session_dir}")
        print(f"📊 Dashboard available at: {self.dashboard.dashboard_file}")
        
        # Save comprehensive report
        report_file = self.demo_dir / "autopilot_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📝 Full report saved to: {report_file}")
        
        return results


async def main():
    demo = AutoPilotDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())