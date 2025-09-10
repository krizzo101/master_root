#!/usr/bin/env python3
"""
Parallel Monitoring Agent Spawner
Uses similar patterns to EnhancedOrchestrator for spawning 5 monitoring agents
"""

import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MonitoringAgent:
    """Individual monitoring agent configuration"""

    def __init__(self, name: str, task: str, timeout: int = 120):
        self.name = name
        self.task = task
        self.timeout = timeout
        self.job_id = f"{name}_{uuid.uuid4().hex[:8]}"
        self.started_at = None
        self.process = None


class ParallelMonitorOrchestrator:
    """Orchestrator for parallel monitoring agents"""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.results_dir = self.project_path / ".monitor-results"
        self.results_dir.mkdir(exist_ok=True)
        self.active_agents: Dict[str, MonitoringAgent] = {}

    async def spawn_monitoring_agents(self) -> Dict[str, Any]:
        """Spawn 5 parallel monitoring agents with short tasks"""

        # Define the 5 monitoring agents
        agents = [
            MonitoringAgent(
                "FileCounter",
                "List and count files by type in current directory using find and awk/sort commands",
                90,
            ),
            MonitoringAgent(
                "GitMonitor",
                "Check git status and show last 5 commits with --oneline format",
                60,
            ),
            MonitoringAgent(
                "SystemResources",
                "Monitor system resources: df -h, free -h, and ps aux | head -10",
                90,
            ),
            MonitoringAgent(
                "LargestFiles",
                "Find top 10 largest files in project using find and sort commands",
                120,
            ),
            MonitoringAgent(
                "CodeCounter",
                "Count lines of code by language using find and wc commands for common extensions",
                90,
            ),
        ]

        print("🚀 Starting Parallel Monitoring Agents")
        print("=" * 60)

        # Start all agents in parallel
        tasks = []
        for agent in agents:
            self.active_agents[agent.job_id] = agent
            task = asyncio.create_task(self._execute_agent(agent))
            tasks.append(task)
            print(f"📊 Agent {agent.name} ({agent.job_id}) - {agent.task[:50]}...")

        print(f"\n⏳ Running {len(agents)} agents in parallel...")

        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile final results
        final_results = {
            "started_at": datetime.now().isoformat(),
            "agents": {},
            "summary": {
                "total_agents": len(agents),
                "successful": 0,
                "failed": 0,
                "total_duration": 0,
            },
        }

        for i, (agent, result) in enumerate(zip(agents, results)):
            if isinstance(result, Exception):
                final_results["agents"][agent.name] = {
                    "job_id": agent.job_id,
                    "status": "error",
                    "error": str(result),
                    "task": agent.task,
                }
                final_results["summary"]["failed"] += 1
            else:
                final_results["agents"][agent.name] = result
                if result.get("status") == "completed":
                    final_results["summary"]["successful"] += 1
                else:
                    final_results["summary"]["failed"] += 1
                final_results["summary"]["total_duration"] += result.get(
                    "duration_seconds", 0
                )

        # Save results
        results_file = (
            self.results_dir
            / f"monitor_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(final_results, f, indent=2)

        print("\n" + "=" * 60)
        print("📈 MONITORING RESULTS:")
        print(f"✅ Successful: {final_results['summary']['successful']}")
        print(f"❌ Failed: {final_results['summary']['failed']}")
        print(f"⏱️  Total Duration: {final_results['summary']['total_duration']:.1f}s")
        print(f"💾 Results saved to: {results_file}")
        print("=" * 60)

        return final_results

    async def _execute_agent(self, agent: MonitoringAgent) -> Dict[str, Any]:
        """Execute a single monitoring agent"""

        agent.started_at = datetime.now()

        # Build the monitoring command based on agent type
        cmd = self._build_monitoring_command(agent)

        try:
            # Start the process
            agent.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_path),
            )

            # Wait for completion with timeout
            stdout, stderr = agent.process.communicate(timeout=agent.timeout)

            duration = (datetime.now() - agent.started_at).total_seconds()

            result = {
                "job_id": agent.job_id,
                "name": agent.name,
                "task": agent.task,
                "status": "completed" if agent.process.returncode == 0 else "failed",
                "return_code": agent.process.returncode,
                "duration_seconds": duration,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "started_at": agent.started_at.isoformat(),
                "completed_at": datetime.now().isoformat(),
            }

            # Save individual agent result
            agent_file = self.results_dir / f"{agent.job_id}_result.json"
            with open(agent_file, "w") as f:
                json.dump(result, f, indent=2)

            status_symbol = "✅" if result["status"] == "completed" else "❌"
            print(f"{status_symbol} {agent.name} completed in {duration:.1f}s")

            return result

        except subprocess.TimeoutExpired:
            if agent.process:
                agent.process.kill()

            duration = (datetime.now() - agent.started_at).total_seconds()

            result = {
                "job_id": agent.job_id,
                "name": agent.name,
                "task": agent.task,
                "status": "timeout",
                "duration_seconds": duration,
                "error": f"Agent timed out after {agent.timeout}s",
                "started_at": agent.started_at.isoformat(),
                "completed_at": datetime.now().isoformat(),
            }

            print(f"⏰ {agent.name} timed out after {agent.timeout}s")
            return result

        except Exception as e:
            duration = (datetime.now() - agent.started_at).total_seconds()

            result = {
                "job_id": agent.job_id,
                "name": agent.name,
                "task": agent.task,
                "status": "error",
                "duration_seconds": duration,
                "error": str(e),
                "started_at": agent.started_at.isoformat(),
                "completed_at": datetime.now().isoformat(),
            }

            print(f"💥 {agent.name} failed: {e}")
            return result

    def _build_monitoring_command(self, agent: MonitoringAgent) -> List[str]:
        """Build appropriate command for each monitoring agent type"""

        if agent.name == "FileCounter":
            return [
                "bash",
                "-c",
                "echo '=== FILE COUNT BY TYPE ===' && "
                "find . -type f | sed 's/.*\\.//g' | sort | uniq -c | sort -nr | head -20 && "
                "echo && echo 'Total files:' $(find . -type f | wc -l) && "
                "echo 'Total directories:' $(find . -type d | wc -l)",
            ]

        elif agent.name == "GitMonitor":
            return [
                "bash",
                "-c",
                "echo '=== GIT STATUS ===' && git status --porcelain && "
                "echo && echo '=== RECENT COMMITS ===' && "
                "git log --oneline -5",
            ]

        elif agent.name == "SystemResources":
            return [
                "bash",
                "-c",
                "echo '=== DISK USAGE ===' && df -h && "
                "echo && echo '=== MEMORY USAGE ===' && free -h && "
                "echo && echo '=== TOP PROCESSES ===' && ps aux | head -10",
            ]

        elif agent.name == "LargestFiles":
            return [
                "bash",
                "-c",
                "echo '=== LARGEST FILES ===' && "
                "find . -type f -exec du -h {} + 2>/dev/null | sort -hr | head -15",
            ]

        elif agent.name == "CodeCounter":
            return [
                "bash",
                "-c",
                "echo '=== LINES OF CODE BY LANGUAGE ===' && "
                "echo 'Python:' $(find . -name '*.py' -exec wc -l {} + 2>/dev/null | tail -1) && "
                "echo 'JavaScript:' $(find . -name '*.js' -exec wc -l {} + 2>/dev/null | tail -1) && "
                "echo 'TypeScript:' $(find . -name '*.ts' -exec wc -l {} + 2>/dev/null | tail -1) && "
                "echo 'Shell:' $(find . -name '*.sh' -exec wc -l {} + 2>/dev/null | tail -1) && "
                "echo 'JSON:' $(find . -name '*.json' -exec wc -l {} + 2>/dev/null | tail -1) && "
                "echo 'Markdown:' $(find . -name '*.md' -exec wc -l {} + 2>/dev/null | tail -1)",
            ]

        else:
            # Fallback generic command
            return ["echo", f"Unknown agent type: {agent.name}"]


async def main():
    """Main execution function"""
    orchestrator = ParallelMonitorOrchestrator(Path.cwd())
    results = await orchestrator.spawn_monitoring_agents()
    return results


if __name__ == "__main__":
    asyncio.run(main())
