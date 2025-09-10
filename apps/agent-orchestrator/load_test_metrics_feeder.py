#!/usr/bin/env python3
"""
Load Test Metrics Feeder
Simulates real-time metrics from active orchestrator workflows for dashboard testing
"""
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from monitoring.metrics_collector import MetricType, get_global_collector


class LiveMetricsFeeder:
    """Feeds live metrics from active orchestrator workflows"""

    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)
        self.collector = get_global_collector()
        self.running = False
        self.active_workflows = {}

    async def scan_active_workflows(self) -> Dict[str, Dict]:
        """Scan for active workflows based on running processes and recent log activity"""
        workflows = {}

        # Find all workflow directories with recent activity
        for workflow_dir in self.outputs_dir.rglob("*/"):
            if workflow_dir.is_dir():
                # Check for logs directory
                logs_dir = workflow_dir / "logs"
                if logs_dir.exists():
                    # Check for recent log activity (last 10 minutes)
                    recent_activity = False
                    for log_file in logs_dir.glob("*.log"):
                        if log_file.stat().st_mtime > time.time() - 600:  # 10 minutes
                            recent_activity = True
                            break

                    if recent_activity:
                        workflow_id = f"{workflow_dir.parent.name}_{workflow_dir.name}"
                        workflows[workflow_id] = {
                            "path": str(workflow_dir),
                            "logs_dir": str(logs_dir),
                            "started": workflow_dir.stat().st_ctime,
                            "last_activity": max(
                                [
                                    f.stat().st_mtime
                                    for f in logs_dir.glob("*")
                                    if f.is_file()
                                ],
                                default=0,
                            ),
                        }

        return workflows

    def generate_realistic_metrics(self, workflow_id: str, workflow_info: Dict):
        """Generate realistic metrics for a workflow"""
        now = time.time()

        # Task metrics (simulate ongoing work)
        if random.random() < 0.3:  # 30% chance of task event per cycle
            if random.random() < 0.7:  # 70% completion, 30% start
                self.collector.record_task_completed(
                    task_id=f"{workflow_id}_task_{random.randint(1000, 9999)}",
                    execution_time=random.uniform(0.5, 30.0),
                    success=random.random() < 0.85,  # 85% success rate
                    metadata={"workflow": workflow_id},
                )
            else:
                self.collector.record_task_started(
                    task_id=f"{workflow_id}_task_{random.randint(1000, 9999)}",
                    metadata={"workflow": workflow_id},
                )

        # Token usage (simulate AI calls)
        if random.random() < 0.4:  # 40% chance of token usage
            self.collector.record_token_usage(
                model_name=random.choice(
                    ["gpt-4", "claude-3.5-sonnet", "gpt-3.5-turbo"]
                ),
                prompt_tokens=random.randint(1000, 8000),
                completion_tokens=random.randint(200, 2000),
                total_tokens=None,  # Will be calculated
                cost=None,  # Will be estimated
                metadata={"workflow": workflow_id},
            )

        # Memory and resource usage
        if random.random() < 0.2:  # 20% chance
            self.collector.record_metric(
                metric_type=MetricType.MEMORY_USAGE,
                value=random.uniform(50, 500),  # MB
                metadata={"workflow": workflow_id},
            )

        # Queue depth
        if random.random() < 0.1:  # 10% chance
            self.collector.record_metric(
                metric_type=MetricType.QUEUE_DEPTH,
                value=random.randint(0, 20),
                metadata={"workflow": workflow_id},
            )

    async def start_feeding(self, interval: float = 2.0):
        """Start feeding metrics at regular intervals"""
        self.running = True
        print(f"🔄 Starting metrics feeder (interval: {interval}s)")

        while self.running:
            try:
                # Scan for active workflows
                workflows = await self.scan_active_workflows()

                if workflows != self.active_workflows:
                    print(
                        f"📊 Updated workflow monitoring: {len(workflows)} active workflows"
                    )
                    for wf_id in workflows:
                        if wf_id not in self.active_workflows:
                            print(f"  ✅ Started monitoring: {wf_id}")
                    for wf_id in self.active_workflows:
                        if wf_id not in workflows:
                            print(f"  ❌ Stopped monitoring: {wf_id}")

                    self.active_workflows = workflows

                # Generate metrics for each active workflow
                for workflow_id, workflow_info in workflows.items():
                    self.generate_realistic_metrics(workflow_id, workflow_info)

                # Wait for next cycle
                await asyncio.sleep(interval)

            except Exception as e:
                print(f"❌ Error in metrics feeding: {e}")
                await asyncio.sleep(interval)

    def stop_feeding(self):
        """Stop feeding metrics"""
        self.running = False
        print("🛑 Stopping metrics feeder")


async def main():
    """Main function for testing"""
    feeder = LiveMetricsFeeder()

    try:
        await feeder.start_feeding(interval=1.0)  # Fast interval for testing
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        feeder.stop_feeding()


if __name__ == "__main__":
    print("🚀 Live Metrics Feeder for Dashboard Load Testing")
    print("This will generate realistic metrics from active orchestrator workflows")
    print("Press Ctrl+C to stop\n")

    asyncio.run(main())
