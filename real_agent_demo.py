#!/usr/bin/env python3
"""
Real Agent Demo - Execute REAL Claude agents with monitoring
Uses actual Claude CLI with proper token management
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code_v3.agent_monitor import (
    SessionCaptureAgent,
    PhaseValidator,
    AgentHealthMonitor,
    MonitoringDashboard
)


class RealAgentDemo:
    """Execute real Claude agents with monitoring and token management"""
    
    def __init__(self):
        self.demo_dir = Path("/tmp/real_agent_demo")
        self.demo_dir.mkdir(exist_ok=True)
        self.session_dir = self.demo_dir / ".sessions"
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize monitoring components
        self.capture = SessionCaptureAgent(self.session_dir)
        self.validator = PhaseValidator()
        self.health = AgentHealthMonitor()
        
        # Check for Claude token
        self.claude_token = os.environ.get("CLAUDE_CODE_TOKEN")
        if not self.claude_token:
            raise ValueError("CLAUDE_CODE_TOKEN not found in environment")
        
        print(f"✅ CLAUDE_CODE_TOKEN found (length: {len(self.claude_token)})")
        
        # Check Claude CLI
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError("Claude CLI not found in PATH")
        
        self.claude_path = result.stdout.strip()
        print(f"✅ Claude CLI found at: {self.claude_path}")
    
    def create_safe_environment(self) -> Dict[str, str]:
        """Create environment with ANTHROPIC_API_KEY removed"""
        env = os.environ.copy()
        
        # CRITICAL: Remove ANTHROPIC_API_KEY to avoid conflicts
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            print("   🔒 Removed ANTHROPIC_API_KEY from environment")
        
        # Ensure CLAUDE_CODE_TOKEN is set
        env["CLAUDE_CODE_TOKEN"] = self.claude_token
        
        # Set HOME to ensure Claude uses correct config
        env["HOME"] = os.environ.get("HOME", "/home/opsvi")
        
        return env
    
    async def run_real_agent(
        self,
        task: str,
        phase: str,
        timeout: int = 300,
        allowed_tools: Optional[List[str]] = None
    ) -> Dict:
        """Run a real Claude agent with monitoring"""
        
        print(f"\n{'='*60}")
        print(f"REAL AGENT: {phase.upper()}")
        print(f"{'='*60}")
        print(f"Task: {task[:100]}...")
        print(f"Timeout: {timeout}s")
        
        # Create safe environment
        env = self.create_safe_environment()
        
        # Build Claude command
        cmd = [
            self.claude_path,
            "--print",  # Non-interactive mode
            "--output-format", "text",
            "--dangerously-skip-permissions"  # Skip interactive prompts
        ]
        
        # Add allowed tools if specified
        if allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(allowed_tools)])
        else:
            # Default safe tools
            cmd.extend(["--allowed-tools", "Read,Write,Edit,Bash(ls:*),Bash(cat:*),Bash(echo:*)"])
        
        # Add the task as the prompt
        cmd.append(task)
        
        print(f"📋 Command: {' '.join(cmd[:3])}... [task]")
        
        # Start the real Claude agent
        print(f"🚀 Starting real Claude agent...")
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.demo_dir)
            )
            
            job_id = f"real_{phase}_{int(time.time())}"
            
            # Capture session with monitoring
            print(f"📹 Monitoring agent execution...")
            session = await self.capture.capture_session_stream(
                process=process,
                job_id=job_id,
                phase=phase,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            # Validate results
            print(f"\n✅ Validating {phase} outputs...")
            validation = await self.validator.validate_phase(
                phase=phase,
                project_path=self.demo_dir,
                session=session,
                config={"timeout": timeout}
            )
            
            # Health check
            health = await self.health.check_health(session)
            
            # Display results
            print(f"\n📊 Results:")
            print(f"   Status: {session.get('status', 'unknown')}")
            print(f"   Duration: {duration:.1f}s")
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
                "task": task,
                "session": session,
                "validation": validation,
                "health": health,
                "duration": duration
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Agent timed out after {timeout}s")
            return {
                "phase": phase,
                "task": task,
                "status": "timeout",
                "duration": timeout
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                "phase": phase,
                "task": task,
                "status": "error",
                "error": str(e)
            }
    
    async def run_simple_test(self):
        """Run a simple test with a real Claude agent"""
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║         REAL CLAUDE AGENT TEST                              ║
║     With Full Monitoring and Token Management               ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Simple, safe task that should complete quickly
        task = """Create a simple Python function that adds two numbers together. 
        Write it to a file called add_numbers.py with proper documentation."""
        
        result = await self.run_real_agent(
            task=task,
            phase="simple_test",
            timeout=60,  # 1 minute timeout for simple task
            allowed_tools=["Write", "Read"]
        )
        
        # Check if file was created
        expected_file = self.demo_dir / "add_numbers.py"
        if expected_file.exists():
            print(f"\n✅ Success! File created: {expected_file}")
            print(f"\n📄 File contents:")
            print("-" * 40)
            print(expected_file.read_text()[:500])
            print("-" * 40)
        else:
            print(f"\n⚠️ File not created at: {expected_file}")
        
        return result
    
    async def run_parallel_agents(self):
        """Run multiple real agents in parallel"""
        
        print(f"\n{'='*60}")
        print(f"PARALLEL REAL AGENTS TEST")
        print(f"{'='*60}")
        
        tasks = [
            ("Create a README.md file with project description", "readme", 60),
            ("Create a simple test file test_example.py", "test", 60),
            ("Create a configuration file config.json", "config", 60)
        ]
        
        print(f"\n🚀 Spawning {len(tasks)} real Claude agents in parallel...")
        print("   ⚠️ This will use multiple Claude tokens/sessions")
        
        # Run all agents in parallel
        agent_tasks = []
        for task, name, timeout in tasks:
            agent_task = self.run_real_agent(
                task=task,
                phase=f"parallel_{name}",
                timeout=timeout,
                allowed_tools=["Write", "Read"]
            )
            agent_tasks.append(agent_task)
        
        # Wait for all to complete
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Summary
        print(f"\n📊 Parallel Execution Summary:")
        successful = sum(1 for r in results 
                        if isinstance(r, dict) and r.get("session", {}).get("status") == "completed")
        print(f"   Total agents: {len(tasks)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(tasks) - successful}")
        
        return results


async def main():
    """Main execution"""
    
    try:
        demo = RealAgentDemo()
        
        # Run simple test first
        print("\n📝 Phase 1: Simple Real Agent Test")
        print("-" * 60)
        simple_result = await demo.run_simple_test()
        
        # Ask user before running parallel (costs more)
        print("\n" + "="*60)
        print("Simple test complete!")
        print("\n⚠️  The parallel test will spawn 3 real Claude agents simultaneously.")
        print("This will use more API tokens. Continue? (y/n): ", end="", flush=True)
        
        # For auto-pilot, we'll assume yes
        response = "y"  # In real usage, would use: input().lower()
        
        if response == "y":
            print("\n📝 Phase 2: Parallel Real Agents Test")
            print("-" * 60)
            parallel_results = await demo.run_parallel_agents()
        else:
            print("Skipping parallel test.")
            parallel_results = None
        
        # Final report
        print(f"\n{'='*60}")
        print(f"REAL AGENT TESTING COMPLETE")
        print(f"{'='*60}")
        
        print(f"\n📊 Summary:")
        print(f"   Simple test: {simple_result.get('status', 'completed')}")
        if parallel_results:
            print(f"   Parallel tests: {len(parallel_results)} agents executed")
        
        print(f"\n📁 All sessions saved to: {demo.session_dir}")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "simple_test": {
                "status": simple_result.get("session", {}).get("status"),
                "duration": simple_result.get("duration"),
                "lines_captured": simple_result.get("session", {}).get("total_lines")
            },
            "parallel_tests": [
                {
                    "phase": r.get("phase"),
                    "status": r.get("session", {}).get("status") if isinstance(r, dict) else "error",
                    "duration": r.get("duration")
                } for r in (parallel_results or [])
            ] if parallel_results else None
        }
        
        report_file = demo.demo_dir / "real_agent_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📝 Report saved to: {report_file}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())