#!/usr/bin/env python3
"""
Meta-System Orchestrator

Main entry point for the self-improving meta-system that uses the project's
own capabilities to complete itself.
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-meta")

import argparse  # noqa: E402
import asyncio  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict, List, Optional  # noqa: E402

from opsvi_meta.implementation_pipeline import ImplementationPipeline  # noqa: E402

# Import from the meta library
from opsvi_meta.todo_discovery import TodoDiscoveryEngine  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/opsvi/master_root/logs/meta_system.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MetaSystemOrchestrator:
    """Main orchestrator for the self-improving meta-system"""

    def __init__(self, project_root: str = "/home/opsvi/master_root"):
        self.project_root = Path(project_root)
        self.discovery_engine = TodoDiscoveryEngine(project_root)
        self.implementation_pipeline = ImplementationPipeline(project_root)

        # Create necessary directories
        self.data_dir = self.project_root / ".meta-system"
        self.data_dir.mkdir(exist_ok=True)

        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        self.checkpoints_dir = self.data_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)

    def discover_todos(self, export: bool = True) -> List[Any]:
        """Discover all TODOs in the codebase"""

        logger.info("Starting TODO discovery...")

        todos = self.discovery_engine.discover_todos()

        logger.info(f"Discovered {len(todos)} TODO items")

        if export:
            export_path = (
                self.data_dir / f"todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            self.discovery_engine.export_to_json(str(export_path))
            logger.info(f"Exported TODOs to {export_path}")

        # Generate summary
        classifications = self.discovery_engine.classify_todos()

        print("\n" + "=" * 60)
        print("TODO DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"Total TODOs found: {len(todos)}")
        print("\nBy Category:")
        for category, items in classifications["by_category"].items():
            print(f"  {category}: {len(items)}")

        print("\nBy Complexity:")
        for complexity, items in classifications["by_complexity"].items():
            print(f"  {complexity}: {len(items)}")

        print("\nBy Priority (1=low, 5=high):")
        for priority, items in classifications["by_priority"].items():
            print(f"  Priority {priority}: {len(items)}")

        print("\nBy Suggested Agent:")
        for agent, items in classifications["by_agent"].items():
            print(f"  {agent}: {len(items)}")

        print("=" * 60 + "\n")

        return todos

    async def implement_todos(
        self,
        max_items: int = 10,
        complexity_filter: Optional[str] = None,
        dry_run: bool = False,
    ):
        """Implement discovered TODOs"""

        logger.info("Starting TODO implementation...")

        # Get implementation queue
        todos = self.discovery_engine.get_implementation_queue(
            max_items=max_items, complexity_filter=complexity_filter
        )

        if not todos:
            logger.info("No TODOs to implement")
            return

        print(f"\n📋 Implementation Queue ({len(todos)} items):")
        for i, todo in enumerate(todos, 1):
            print(f"{i}. [{todo.category}] {todo.file_path}:{todo.line_number}")
            print(f"   {todo.content[:80]}...")
            print(
                f"   Priority: {todo.priority}, Complexity: {todo.estimated_complexity}"
            )
            print(f"   Agent: {todo.suggested_agent}")

        if dry_run:
            print("\n🔍 Dry run mode - no changes will be made")
            return

        # Confirm before proceeding
        response = input("\n⚠️  Proceed with implementation? (yes/no): ")
        if response.lower() != "yes":
            print("Implementation cancelled")
            return

        # Run implementations
        print("\n🚀 Starting implementations...")
        await self.implementation_pipeline.run_batch_implementation(
            todos=todos, max_parallel=3
        )

        # Generate report
        report = self.implementation_pipeline.generate_report()

        print("\n" + "=" * 60)
        print("IMPLEMENTATION RESULTS")
        print("=" * 60)
        print(f"Total attempted: {report['summary']['total_attempted']}")
        print(f"Successful: {report['summary']['successful']}")
        print(f"Partial: {report['summary']['partial']}")
        print(f"Failed: {report['summary']['failed']}")
        print(
            f"Total duration: {report['summary']['total_duration_seconds']:.2f} seconds"
        )
        print(f"Files modified: {len(report['files_modified'])}")
        print(f"Tests added: {len(report['tests_added'])}")

        if report["failures"]:
            print("\n❌ Failures:")
            for failure in report["failures"]:
                print(f"  - {failure['todo_id']}: {failure['error']}")

        # Save report
        report_path = (
            self.reports_dir
            / f"implementation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📊 Full report saved to: {report_path}")

    def create_dashboard(self):
        """Create a monitoring dashboard"""

        dashboard_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Meta-System Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        .progress { background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; margin-top: 10px; }
        .progress-bar { background: #27ae60; height: 100%; transition: width 0.3s; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #34495e; color: white; }
        .status-success { color: #27ae60; }
        .status-failure { color: #e74c3c; }
        .status-partial { color: #f39c12; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 OpsVi Meta-System Dashboard</h1>
        <p>Self-Improving System Status</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value" id="total-todos">0</div>
            <div class="stat-label">Total TODOs</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="completed-todos">0</div>
            <div class="stat-label">Completed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="success-rate">0%</div>
            <div class="stat-label">Success Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="tests-added">0</div>
            <div class="stat-label">Tests Added</div>
        </div>
    </div>

    <div class="progress">
        <div class="progress-bar" id="completion-progress" style="width: 0%"></div>
    </div>

    <h2>Recent Implementations</h2>
    <table id="implementations-table">
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>File</th>
                <th>TODO</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Agent</th>
            </tr>
        </thead>
        <tbody>
            <!-- Populated dynamically -->
        </tbody>
    </table>

    <script>
        // Auto-refresh every 30 seconds
        setInterval(() => {
            fetch('/api/meta-system/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-todos').textContent = data.total_todos;
                    document.getElementById('completed-todos').textContent = data.completed_todos;
                    document.getElementById('success-rate').textContent = data.success_rate + '%';
                    document.getElementById('tests-added').textContent = data.tests_added;
                    document.getElementById('completion-progress').style.width = data.completion_percentage + '%';
                });
        }, 30000);
    </script>
</body>
</html>
        """

        dashboard_path = self.data_dir / "dashboard.html"
        with open(dashboard_path, "w") as f:
            f.write(dashboard_content)

        print(f"📊 Dashboard created at: {dashboard_path}")
        print(f"Open in browser: file://{dashboard_path}")

    def generate_stats(self) -> Dict[str, Any]:
        """Generate current statistics"""

        # Load latest TODO discovery
        todo_files = sorted(self.data_dir.glob("todos_*.json"))
        if not todo_files:
            return {}

        with open(todo_files[-1], "r") as f:
            todo_data = json.load(f)

        # Load implementation reports
        report_files = sorted(self.reports_dir.glob("implementation_*.json"))

        total_implemented = 0
        total_successful = 0
        total_tests = 0

        for report_file in report_files:
            with open(report_file, "r") as f:
                report = json.load(f)
                total_implemented += report["summary"]["total_attempted"]
                total_successful += report["summary"]["successful"]
                total_tests += len(report.get("tests_added", []))

        stats = {
            "total_todos": todo_data["metadata"]["total_todos"],
            "completed_todos": total_successful,
            "completion_percentage": round(
                (total_successful / todo_data["metadata"]["total_todos"]) * 100, 2
            )
            if todo_data["metadata"]["total_todos"] > 0
            else 0,
            "success_rate": round((total_successful / total_implemented) * 100, 2)
            if total_implemented > 0
            else 0,
            "tests_added": total_tests,
            "last_updated": datetime.now().isoformat(),
        }

        return stats


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="OpsVi Meta-System Orchestrator")
    parser.add_argument(
        "command",
        choices=["discover", "implement", "dashboard", "stats"],
        help="Command to execute",
    )
    parser.add_argument(
        "--max-items", type=int, default=10, help="Maximum number of TODOs to implement"
    )
    parser.add_argument(
        "--complexity",
        choices=["simple", "medium", "complex"],
        help="Filter by complexity",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform dry run without making changes"
    )

    args = parser.parse_args()

    orchestrator = MetaSystemOrchestrator()

    if args.command == "discover":
        orchestrator.discover_todos()

    elif args.command == "implement":
        # First discover TODOs
        orchestrator.discover_todos(export=True)

        # Then implement
        await orchestrator.implement_todos(
            max_items=args.max_items,
            complexity_filter=args.complexity,
            dry_run=args.dry_run,
        )

    elif args.command == "dashboard":
        orchestrator.create_dashboard()

    elif args.command == "stats":
        stats = orchestrator.generate_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
