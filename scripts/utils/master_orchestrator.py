#!/usr/bin/env python3
"""
Master Orchestrator - Unified interface for all monitoring and command capabilities
Brings together commands, monitoring, and multi-agent orchestration
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add libraries to path
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code_v3.enhanced_orchestrator import (
    EnhancedOrchestrator,
    SDLCPhase,
)
from opsvi_mcp.servers.claude_code_v2.server_monitored import (
    MonitoredClaudeCodeV2Server
)
from opsvi_mcp.servers.claude_code_v3.session_debugger import SessionDebugger


class MasterOrchestrator:
    """Unified orchestrator for all capabilities"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.commands_dir = Path("/home/opsvi/master_root/.claude/commands")
        self.v3_orchestrator = EnhancedOrchestrator(self.project_path)
        self.v2_server = MonitoredClaudeCodeV2Server()
        self.debugger = SessionDebugger()
        
        # Track execution history
        self.execution_history = []
        
    async def run_command(self, command: str, *args) -> Dict:
        """Execute a Claude command with monitoring"""
        
        command_path = self.commands_dir / command
        
        # Check if it's a script or markdown
        if command_path.with_suffix('.sh').exists():
            cmd = [str(command_path.with_suffix('.sh'))] + list(args)
        elif command_path.with_suffix('.py').exists():
            cmd = ['python', str(command_path.with_suffix('.py'))] + list(args)
        elif command_path.with_suffix('.md').exists():
            # Markdown commands are documentation
            with open(command_path.with_suffix('.md')) as f:
                return {"type": "documentation", "content": f.read()}
        else:
            return {"error": f"Command {command} not found"}
        
        # Run with monitoring
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        execution = {
            "command": command,
            "args": args,
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        self.execution_history.append(execution)
        return execution
    
    async def run_sdlc_with_commands(
        self,
        project_name: str,
        requirements: str,
        use_commands: List[str] = None
    ) -> Dict:
        """Run SDLC with integrated commands"""
        
        use_commands = use_commands or [
            "context-prime",
            "sdlc-preflight-enhanced",
            "project-session-start"
        ]
        
        results = {"phases": {}, "commands": {}}
        
        # Run pre-SDLC commands
        for cmd in use_commands:
            print(f"Running command: /{cmd}")
            results["commands"][cmd] = await self.run_command(cmd, project_name)
        
        # Run SDLC phases with monitoring
        phases = [
            SDLCPhase.DISCOVERY,
            SDLCPhase.DESIGN,
            SDLCPhase.PLANNING,
            SDLCPhase.DEVELOPMENT,
            SDLCPhase.TESTING
        ]
        
        sdlc_result = await self.v3_orchestrator.execute_sdlc_lifecycle(
            project_name=project_name,
            requirements=requirements,
            phases_to_run=phases
        )
        
        results["sdlc"] = sdlc_result
        
        # Run post-SDLC commands
        post_commands = [
            "sdlc-session-exporter",
            "sdlc-violation-analyzer",
            "docs-comprehensive"
        ]
        
        for cmd in post_commands:
            results["commands"][cmd] = await self.run_command(cmd)
        
        return results
    
    async def parallel_task_execution(
        self,
        tasks: List[str],
        mode: str = "parallel"
    ) -> Dict:
        """Execute multiple tasks with monitoring"""
        
        if mode == "parallel":
            # Use V2 for parallel execution
            result = await self.v2_server.spawn_parallel_monitored_agents(
                tasks=tasks,
                timeout=600,
                max_concurrent=5,
                enable_monitoring=True
            )
        else:
            # Sequential execution with V3
            results = []
            for task in tasks:
                agent_result = await self.v2_server.spawn_monitored_agent(
                    task=task,
                    timeout=600,
                    enable_monitoring=True
                )
                results.append(agent_result)
                
                # Wait for completion
                await asyncio.sleep(2)
                status = await self.v2_server.get_agent_status(
                    agent_result["job_id"]
                )
                results[-1]["final_status"] = status
            
            result = {"tasks": results}
        
        return result
    
    async def debug_failed_agents(self) -> Dict:
        """Find and debug all failed agents"""
        
        session_dir = self.project_path / ".sdlc-sessions"
        failed_sessions = []
        
        if session_dir.exists():
            for phase_dir in session_dir.iterdir():
                if phase_dir.is_dir():
                    for job_dir in phase_dir.iterdir():
                        if job_dir.is_dir():
                            summary_file = job_dir / "session_summary.json"
                            if summary_file.exists():
                                with open(summary_file) as f:
                                    summary = json.load(f)
                                
                                if summary.get("status") != "completed":
                                    # Debug this session
                                    self.debugger.debug_session(job_dir.name)
                                    failed_sessions.append({
                                        "job_id": job_dir.name,
                                        "phase": phase_dir.name,
                                        "status": summary.get("status"),
                                        "errors": summary.get("errors", [])
                                    })
        
        return {
            "failed_count": len(failed_sessions),
            "sessions": failed_sessions
        }
    
    async def run_tdd_workflow(
        self,
        feature_name: str,
        requirements: str
    ) -> Dict:
        """Run TDD workflow with monitoring"""
        
        # 1. Create failing tests
        test_agent = await self.v2_server.spawn_monitored_agent(
            task=f"Create comprehensive tests for {feature_name}: {requirements}",
            timeout=300,
            enable_monitoring=True
        )
        
        # 2. Run tests (should fail)
        test_run1 = await self.run_command("tdd-monitored", feature_name)
        
        # 3. Implement feature
        impl_agent = await self.v2_server.spawn_monitored_agent(
            task=f"Implement {feature_name} to pass the tests",
            timeout=600,
            enable_monitoring=True
        )
        
        # 4. Run tests again (should pass)
        test_run2 = await self.run_command("tdd-monitored", feature_name)
        
        # 5. Refactor if needed
        if test_run2["return_code"] == 0:
            refactor_agent = await self.v2_server.spawn_monitored_agent(
                task=f"Refactor {feature_name} for better performance and readability",
                timeout=300,
                enable_monitoring=True
            )
        
        return {
            "feature": feature_name,
            "test_creation": test_agent,
            "initial_test_run": test_run1,
            "implementation": impl_agent,
            "final_test_run": test_run2,
            "refactoring": refactor_agent if test_run2["return_code"] == 0 else None
        }
    
    async def generate_comprehensive_report(self) -> Dict:
        """Generate report of all activities"""
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "project_path": str(self.project_path),
            "execution_history": self.execution_history,
            "sessions": {},
            "metrics": {}
        }
        
        # Collect all sessions
        session_dir = self.project_path / ".sdlc-sessions"
        if session_dir.exists():
            for phase_dir in session_dir.iterdir():
                if phase_dir.is_dir():
                    phase_sessions = []
                    for job_dir in phase_dir.iterdir():
                        if job_dir.is_dir():
                            summary_file = job_dir / "session_summary.json"
                            if summary_file.exists():
                                with open(summary_file) as f:
                                    phase_sessions.append(json.load(f))
                    
                    report["sessions"][phase_dir.name] = phase_sessions
        
        # Calculate metrics
        total_duration = sum(
            s.get("duration_seconds", 0)
            for sessions in report["sessions"].values()
            for s in sessions
        )
        
        total_errors = sum(
            len(s.get("errors", []))
            for sessions in report["sessions"].values()
            for s in sessions
        )
        
        success_rate = sum(
            1 for sessions in report["sessions"].values()
            for s in sessions
            if s.get("status") == "completed"
        ) / max(sum(len(sessions) for sessions in report["sessions"].values()), 1)
        
        report["metrics"] = {
            "total_duration_seconds": total_duration,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "total_sessions": sum(len(sessions) for sessions in report["sessions"].values())
        }
        
        # Save report
        report_file = self.project_path / f"master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {report_file}")
        return report


async def main():
    """Example usage of master orchestrator"""
    
    orchestrator = MasterOrchestrator()
    
    # Example 1: Run SDLC with commands
    print("Running SDLC with integrated commands...")
    result = await orchestrator.run_sdlc_with_commands(
        project_name="test-project",
        requirements="Create a simple REST API"
    )
    
    # Example 2: Parallel task execution
    print("\nRunning parallel tasks...")
    parallel_result = await orchestrator.parallel_task_execution(
        tasks=[
            "Analyze security vulnerabilities",
            "Check code quality",
            "Review documentation"
        ],
        mode="parallel"
    )
    
    # Example 3: Debug failures
    print("\nDebugging failed agents...")
    debug_result = await orchestrator.debug_failed_agents()
    
    # Example 4: Generate report
    print("\nGenerating comprehensive report...")
    report = await orchestrator.generate_comprehensive_report()
    
    print("\n✅ Master orchestration complete!")
    print(f"   Success rate: {report['metrics']['success_rate']:.1%}")
    print(f"   Total duration: {report['metrics']['total_duration_seconds']:.1f}s")
    print(f"   Total errors: {report['metrics']['total_errors']}")


if __name__ == "__main__":
    asyncio.run(main())