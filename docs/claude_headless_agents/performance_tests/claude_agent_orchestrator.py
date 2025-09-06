#!/usr/bin/env python3
"""
Claude Agent Orchestrator
Manages multiple headless Claude agents in parallel with monitoring and result collection.
"""

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ClaudeAgent:
    """Represents a single Claude agent instance."""

    def __init__(
        self,
        agent_type: str,
        model: str = "sonnet",
        system_prompt: str = "",
        allowed_tools: List[str] = None,
        workspace: str = "./workspace",
    ):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.model = model
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []
        self.workspace = workspace
        self.start_time = None
        self.end_time = None
        self.status = "pending"
        self.result = None
        self.error = None

    def build_command(
        self, prompt: str, additional_flags: List[str] = None
    ) -> List[str]:
        """Build the Claude command with all parameters."""
        cmd = [
            "claude",
            "-p",
            "--model",
            self.model,
            "--output-format",
            "json",
            "--session-id",
            self.agent_id,
        ]

        if self.system_prompt:
            cmd.extend(["--append-system-prompt", self.system_prompt])

        if self.allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(self.allowed_tools)])

        if self.workspace:
            cmd.extend(["--add-dir", self.workspace])

        if additional_flags:
            cmd.extend(additional_flags)

        cmd.extend(["--", prompt])
        return cmd

    def run(
        self, prompt: str, additional_flags: List[str] = None, timeout: int = 300
    ) -> Dict:
        """Execute the agent and return results."""
        self.start_time = time.time()
        self.status = "running"

        cmd = self.build_command(prompt, additional_flags)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            self.end_time = time.time()

            if result.returncode == 0:
                try:
                    self.result = json.loads(result.stdout)
                    self.status = "completed"
                except json.JSONDecodeError:
                    self.result = {"raw_output": result.stdout}
                    self.status = "completed_with_parse_error"
            else:
                self.error = result.stderr
                self.status = "failed"

        except subprocess.TimeoutExpired:
            self.end_time = time.time()
            self.status = "timeout"
            self.error = f"Timeout after {timeout} seconds"
        except Exception as e:
            self.end_time = time.time()
            self.status = "error"
            self.error = str(e)

        return self.get_summary()

    def get_summary(self) -> Dict:
        """Get a summary of the agent execution."""
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "duration": duration,
            "model": self.model,
            "result": self.result.get("result") if self.result else None,
            "error": self.error,
            "cost": self.result.get("total_cost_usd") if self.result else None,
        }


class AgentOrchestrator:
    """Manages multiple Claude agents running in parallel."""

    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel
        self.agents: List[ClaudeAgent] = []
        self.results_queue = queue.Queue()
        self.running_agents = []
        self.lock = threading.Lock()

    def create_agent(self, agent_type: str, **kwargs) -> ClaudeAgent:
        """Create a new agent with predefined configurations."""

        configs = {
            "design": {
                "model": "haiku",
                "system_prompt": "You are a design agent. Create clear, structured designs.",
                "allowed_tools": ["Write", "Read"],
            },
            "development": {
                "model": "sonnet",
                "system_prompt": "You are a development agent. Write clean, tested code.",
                "allowed_tools": ["Write", "Read", "Edit", "Bash"],
            },
            "test": {
                "model": "haiku",
                "system_prompt": "You are a test agent. Write comprehensive tests.",
                "allowed_tools": ["Write", "Read", "Bash"],
            },
            "research": {
                "model": "sonnet",
                "system_prompt": "You are a research agent. Provide detailed analysis.",
                "allowed_tools": ["WebSearch", "WebFetch"],
            },
            "review": {
                "model": "sonnet",
                "system_prompt": "You are a code review agent. Provide constructive feedback.",
                "allowed_tools": ["Read"],
            },
        }

        config = configs.get(agent_type, {})
        config.update(kwargs)

        agent = ClaudeAgent(agent_type=agent_type, **config)
        self.agents.append(agent)
        return agent

    def run_agent_async(
        self, agent: ClaudeAgent, prompt: str, additional_flags: List[str] = None
    ):
        """Run an agent asynchronously."""

        def run_wrapper():
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Starting {agent.agent_type} agent ({agent.agent_id[:8]}...)"
            )
            result = agent.run(prompt, additional_flags)

            with self.lock:
                self.running_agents.remove(agent)

            self.results_queue.put(result)

            status_icon = "✅" if agent.status == "completed" else "❌"
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} {agent.agent_type} agent completed in {result['duration']:.1f}s"
            )

        thread = threading.Thread(target=run_wrapper)

        with self.lock:
            self.running_agents.append(agent)

        thread.start()
        return thread

    def run_pipeline(
        self, tasks: List[Tuple[str, str, Optional[List[str]]]]
    ) -> List[Dict]:
        """
        Run a pipeline of tasks.
        tasks: List of (agent_type, prompt, additional_flags)
        """
        threads = []
        results = []

        print(f"\n{'='*60}")
        print(f"Starting pipeline with {len(tasks)} tasks")
        print(f"Max parallel agents: {self.max_parallel}")
        print(f"{'='*60}\n")

        for i, (agent_type, prompt, flags) in enumerate(tasks):
            # Wait if we're at max parallel capacity
            while len(self.running_agents) >= self.max_parallel:
                time.sleep(0.5)

            agent = self.create_agent(agent_type)
            thread = self.run_agent_async(agent, prompt, flags)
            threads.append(thread)

            # Small delay to avoid overwhelming the system
            time.sleep(1)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect all results
        while not self.results_queue.empty():
            results.append(self.results_queue.get())

        return results

    def run_sequential(
        self, tasks: List[Tuple[str, str, Optional[List[str]]]]
    ) -> List[Dict]:
        """Run tasks sequentially with dependencies."""
        results = []
        workspace = "./sequential_workspace"
        os.makedirs(workspace, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Starting sequential pipeline with {len(tasks)} tasks")
        print(f"{'='*60}\n")

        for i, (agent_type, prompt, flags) in enumerate(tasks):
            print(f"[Step {i+1}/{len(tasks)}] {agent_type.capitalize()} Agent")

            # Pass workspace to maintain context between steps
            agent = self.create_agent(agent_type, workspace=workspace)

            # Add context from previous steps
            if i > 0:
                prompt = f"Previous steps completed. Now: {prompt}"

            result = agent.run(prompt, flags)
            results.append(result)

            if agent.status != "completed":
                print(f"⚠️ Step {i+1} failed. Stopping pipeline.")
                break

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """Generate a summary report of all agent executions."""
        report = []
        report.append("\n" + "=" * 60)
        report.append("EXECUTION SUMMARY")
        report.append("=" * 60 + "\n")

        total_duration = sum(r["duration"] for r in results if r["duration"])
        total_cost = sum(r["cost"] for r in results if r["cost"])
        success_count = sum(1 for r in results if r["status"] == "completed")

        report.append(f"Total Agents Run: {len(results)}")
        report.append(f"Successful: {success_count}/{len(results)}")
        report.append(f"Total Duration: {total_duration:.1f}s")
        report.append(f"Total Cost: ${total_cost:.6f}")
        report.append("")

        report.append("Individual Agent Results:")
        report.append("-" * 40)

        for r in results:
            status_icon = "✅" if r["status"] == "completed" else "❌"
            report.append(f"\n{status_icon} {r['agent_type'].upper()} Agent")
            report.append(f"   ID: {r['agent_id'][:8]}...")
            report.append(f"   Model: {r['model']}")
            report.append(f"   Status: {r['status']}")
            if r["duration"]:
                report.append(f"   Duration: {r['duration']:.1f}s")
            if r["cost"]:
                report.append(f"   Cost: ${r['cost']:.6f}")
            if r["error"]:
                report.append(f"   Error: {r['error'][:100]}...")

        return "\n".join(report)


def example_parallel_execution():
    """Example of running multiple agents in parallel."""
    orchestrator = AgentOrchestrator(max_parallel=3)

    tasks = [
        (
            "design",
            "Design a simple TODO API with CRUD operations",
            ["--dangerously-skip-permissions"],
        ),
        ("research", "Research best practices for REST API design", None),
        (
            "development",
            "Write a Python function for input validation",
            ["--permission-mode", "acceptEdits"],
        ),
    ]

    results = orchestrator.run_pipeline(tasks)
    print(orchestrator.generate_report(results))

    # Save detailed results
    with open("parallel_results.json", "w") as f:
        json.dump(results, f, indent=2)


def example_sequential_execution():
    """Example of running agents sequentially with dependencies."""
    orchestrator = AgentOrchestrator()

    tasks = [
        (
            "design",
            "Create a design for a user authentication system with JWT. Save as design.md",
            None,
        ),
        (
            "development",
            "Read design.md and implement the authentication system in Python. Save as auth.py",
            None,
        ),
        ("test", "Write pytest tests for auth.py. Save as test_auth.py", None),
        (
            "review",
            "Review the code in auth.py and test_auth.py. Provide feedback.",
            None,
        ),
    ]

    results = orchestrator.run_sequential(tasks)
    print(orchestrator.generate_report(results))

    # Save detailed results
    with open("sequential_results.json", "w") as f:
        json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Claude Agent Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["parallel", "sequential", "both"],
        default="both",
        help="Execution mode",
    )
    parser.add_argument(
        "--max-parallel", type=int, default=3, help="Maximum parallel agents"
    )

    args = parser.parse_args()

    if args.mode in ["parallel", "both"]:
        print("\n🚀 Running Parallel Execution Example")
        example_parallel_execution()

    if args.mode in ["sequential", "both"]:
        print("\n📝 Running Sequential Execution Example")
        example_sequential_execution()


if __name__ == "__main__":
    main()
