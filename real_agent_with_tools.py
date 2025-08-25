#!/usr/bin/env python3
"""
Real Agent with Tools - Execute Claude with actual file operations
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code_v3.agent_monitor import (
    SessionCaptureAgent,
    PhaseValidator,
    AgentHealthMonitor
)


class RealAgentWithTools:
    """Execute Claude with tool usage and monitoring"""
    
    def __init__(self):
        self.work_dir = Path("/tmp/real_agent_workspace")
        self.work_dir.mkdir(exist_ok=True)
        self.session_dir = self.work_dir / ".sessions"
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize monitoring
        self.capture = SessionCaptureAgent(self.session_dir)
        self.validator = PhaseValidator()
        self.health = AgentHealthMonitor()
        
        # Verify Claude setup
        self.claude_token = os.environ.get("CLAUDE_CODE_TOKEN")
        if not self.claude_token:
            raise ValueError("CLAUDE_CODE_TOKEN not found")
        print(f"✅ Token ready")
    
    async def run_claude_with_tools(self, task: str, phase: str):
        """Run Claude with actual tool usage"""
        
        print(f"\n{'='*60}")
        print(f"REAL CLAUDE EXECUTION: {phase.upper()}")
        print(f"{'='*60}")
        
        # Create safe environment (remove ANTHROPIC_API_KEY)
        env = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
        env["CLAUDE_CODE_TOKEN"] = self.claude_token
        
        # Create task file for Claude to process
        task_file = self.work_dir / f"{phase}_task.md"
        task_file.write_text(task)
        
        # Build command - using stdin to pass multi-line task
        cmd = [
            "claude",
            "--print",
            "--output-format", "text",
            "--dangerously-skip-permissions",
            "--allowed-tools", "Write,Read,Edit,Bash(echo:*),Bash(cat:*),Bash(ls:*)"
        ]
        
        print(f"📋 Task: {task[:100]}...")
        print(f"🚀 Executing Claude with tools enabled...")
        
        start_time = time.time()
        
        try:
            # Run Claude with the task
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.work_dir)
            )
            
            # Send the task via stdin
            stdout, stderr = process.communicate(input=task, timeout=30)
            
            duration = time.time() - start_time
            
            # Save output
            output_file = self.work_dir / f"{phase}_output.txt"
            output_file.write_text(stdout)
            
            print(f"\n📊 Results:")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Exit code: {process.returncode}")
            print(f"   Output length: {len(stdout)} chars")
            print(f"   Output saved to: {output_file}")
            
            # Check for created files
            created_files = []
            for f in self.work_dir.glob("*"):
                if f.is_file() and f.name not in ["real_agent_report.json", f"{phase}_task.md", f"{phase}_output.txt"]:
                    age = time.time() - f.stat().st_mtime
                    if age < 60:  # Created in last minute
                        created_files.append(f.name)
            
            if created_files:
                print(f"   📄 Files created: {created_files}")
                for fname in created_files:
                    fpath = self.work_dir / fname
                    print(f"\n   Content of {fname}:")
                    print("   " + "-"*40)
                    content = fpath.read_text()[:500]
                    for line in content.split('\n')[:10]:
                        print(f"   {line}")
                    print("   " + "-"*40)
            
            # Create monitoring session manually
            session = {
                "job_id": f"real_{phase}_{int(time.time())}",
                "phase": phase,
                "status": "completed" if process.returncode == 0 else "failed",
                "duration_seconds": duration,
                "stdout": stdout[:1000],
                "stderr": stderr,
                "files_created": created_files,
                "return_code": process.returncode
            }
            
            # Health check
            health = await self.health.check_health(session)
            
            return {
                "phase": phase,
                "duration": duration,
                "files_created": created_files,
                "output_length": len(stdout),
                "health": health
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timed out after 30s")
            process.kill()
            return {"phase": phase, "status": "timeout"}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"phase": phase, "status": "error", "error": str(e)}
    
    async def run_demo(self):
        """Run demonstration with multiple tasks"""
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║         REAL CLAUDE WITH TOOLS DEMONSTRATION                ║
║     Actual Tool Usage with Monitoring                       ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Task 1: Create a Python file
        task1 = """Create a Python file called 'calculator.py' with the following:
1. A function add(a, b) that returns a + b
2. A function multiply(a, b) that returns a * b
3. A main block that tests both functions
Include docstrings for all functions."""
        
        result1 = await self.run_claude_with_tools(task1, "python_creation")
        
        # Task 2: Create a README
        task2 = """Create a README.md file that documents the calculator.py module.
Include:
- Title: Calculator Module
- Description of what it does
- Usage examples
- List of available functions"""
        
        result2 = await self.run_claude_with_tools(task2, "readme_creation")
        
        # Task 3: Create a test file
        task3 = """Create a file called test_calculator.py that:
1. Imports the calculator module
2. Tests the add function with 2 + 3 = 5
3. Tests the multiply function with 4 * 5 = 20
Use simple assert statements."""
        
        result3 = await self.run_claude_with_tools(task3, "test_creation")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"DEMONSTRATION COMPLETE")
        print(f"{'='*60}")
        
        results = [result1, result2, result3]
        total_files = sum(len(r.get("files_created", [])) for r in results)
        
        print(f"\n📊 Summary:")
        print(f"   Tasks executed: 3")
        print(f"   Total files created: {total_files}")
        print(f"   Total duration: {sum(r.get('duration', 0) for r in results):.1f}s")
        
        # List all created files
        print(f"\n📁 Workspace contents:")
        for f in sorted(self.work_dir.glob("*")):
            if f.is_file():
                size = f.stat().st_size
                print(f"   {f.name:30} ({size:,} bytes)")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "tasks": results,
            "workspace": str(self.work_dir)
        }
        
        report_file = self.work_dir / "real_agent_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📝 Full report: {report_file}")
        print(f"🔍 Check workspace: {self.work_dir}")


async def main():
    try:
        demo = RealAgentWithTools()
        await demo.run_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())